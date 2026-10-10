"""DataUpdateCoordinator for SAJ eSolar integration."""
from datetime import datetime, timedelta
import logging
from typing import Any
import time
import json

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, ENDPOINTS, ENDPOINTS_V2, UPDATE_INTERVAL, REGIONS
from .elekeeper import calc_signature, encrypt, generatkey, sign_v2_request

_LOGGER = logging.getLogger(__name__)

# Inverter runningState values, as listed by the Elekeeper web device filter
RUNNING_STATE_NORMAL = 1
RUNNING_STATE_ALARM = 2

class SAJeSolarDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the SAJ eSolar API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        region: str = "eu",
        monitored_plants: list[str] | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.session = session
        self.username = username
        self.password = password
        self.region = region
        self.base_url = REGIONS[region]
        self.base_url_v2 = self.base_url.replace("/api/v1", "/api/v2")
        self.monitored_plants = monitored_plants or []
        self.auth_token = None
        self._warned: set[str] = set()

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        try:
            await self._authenticate()

            plant_data = await self._get_plant_list()
            plants = (plant_data.get("data") or {}).get("list") or []

            plants_data = {}

            for plant_uid in self.monitored_plants:
                plant_info = next((p for p in plants if p.get("plantUid") == plant_uid), None)
                if not plant_info:
                    _LOGGER.warning(
                        "Plant %s not found in the account plant list (%d plants returned), skipping it",
                        plant_uid,
                        len(plants),
                    )
                    continue

                plants_data[plant_uid] = await self._get_plant_data(plant_uid, plant_info)

            return plants_data

        except ConfigEntryAuthFailed as err:
            # There is no reauth flow, keep retrying (the error may be temporary)
            raise UpdateFailed(f"Authentication with the SAJ API failed: {err}") from err
        except UpdateFailed:
            raise
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with the SAJ API: {err!r}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error while fetching SAJ data")
            raise UpdateFailed(f"Unexpected error fetching SAJ data: {err!r}") from err

    async def _get_plant_data(self, plant_uid: str, plant_info: dict[str, Any]) -> dict[str, Any]:
        """Fetch everything the sensors need for a plant.

        Failing to fetch the core data fails the whole update (so sensors
        become unavailable instead of reporting zeros); the extras only log a
        warning and are left empty.
        """
        plant_details = await self._get_plant_details_for_plant(plant_uid)
        query_device = await self._resolve_query_device(plant_uid)
        plant_statistics = await self._post_v2("plant_statistics", {"plantUid": plant_uid, **query_device}, plant_uid)
        energy_flow = await self._post_v2("energy_flow", {"plantUid": plant_uid, **query_device}, plant_uid)
        device_list = await self._get_device_list_for_plant(plant_uid)

        device_sn = None
        if device_list["data"]["list"]:
            device_sn = device_list["data"]["list"][0].get("deviceSn")
        if not device_sn:
            _LOGGER.warning("No inverter found for plant %s, inverter, battery and alarm data will be empty", plant_uid)

        battery_list = await self._optional(plant_uid, "battery list", self._get_battery_list_for_plant(plant_uid))
        battery_info = {}
        device_alarms = {}
        if device_sn:
            battery_info = await self._optional(plant_uid, "battery info", self._get_battery_info(device_sn, plant_uid))
            device_alarms = await self._optional(
                plant_uid, "device alarms", self._get_device_alarms(device_sn, plant_uid)
            )

        return {
            "plant_info": plant_info,
            "plant_details": plant_details,
            "device_list": device_list,
            "battery_list": battery_list,
            "plant_statistics": plant_statistics,
            "energy_flow": energy_flow,
            "battery_info": battery_info,
            "device_alarms": device_alarms,
        }

    async def _optional(self, plant_uid: str, what: str, coro) -> dict[str, Any]:
        """Await a non essential request, logging and swallowing failures."""
        try:
            return await coro
        except (UpdateFailed, aiohttp.ClientError) as err:
            _LOGGER.warning("Could not fetch %s for plant %s, related sensors will be empty: %s", what, plant_uid, err)
            return {}

    async def _authenticate(self) -> None:
        """Authenticate with the SAJ eSolar API using the Elekeeper v2 login.

        The token returned by the v2 login is valid for both v1 and v2
        endpoints, whereas the old v1 login token makes v2 endpoints
        return empty data.
        """
        login_data = {
            "username": self.username,
            "password": encrypt(self.password),
            "rememberMe": False,
            "loginType": 1,
        }

        headers, body = sign_v2_request(login_data)
        url = f"{self.base_url_v2}{ENDPOINTS_V2['login']}"

        async with self.session.post(url, data=body, headers=headers) as resp:
            if resp.status == 401:
                raise ConfigEntryAuthFailed("Invalid authentication (HTTP 401)")
            if resp.status != 200:
                raise UpdateFailed(f"Login failed: HTTP {resp.status} from {url}")

            response_data = await self._read_json(resp, "login")

        err_code = response_data.get("errCode")
        _LOGGER.debug("login: errCode=%s", err_code)
        if err_code not in (None, 0):
            raise ConfigEntryAuthFailed(
                f"Login failed (errCode {err_code}): {response_data.get('errMsg') or 'Unknown error'}"
            )

        data = response_data.get("data") or {}
        if not data.get("token"):
            raise UpdateFailed(f"Login response did not include a token (keys: {sorted(data)})")
        self.auth_token = (data.get("tokenHead") or "Bearer ") + data["token"]

    @staticmethod
    async def _read_json(resp: aiohttp.ClientResponse, what: str) -> dict[str, Any]:
        """Parse a JSON response, regardless of the content type the API sends."""
        text = await resp.text()
        try:
            return json.loads(text)
        except ValueError as err:
            raise UpdateFailed(
                f"Unexpected non-JSON response for {what} (HTTP {resp.status}, {resp.content_type}): {text[:200]}"
            ) from err

    async def _post_v2(self, endpoint: str, body: dict[str, Any], plant_uid: str | None = None) -> dict[str, Any]:
        """POST a signed request to an api/v2 endpoint."""
        headers, raw = sign_v2_request(body, token=self.auth_token)
        url = f"{self.base_url_v2}{ENDPOINTS_V2[endpoint]}"
        where = f"{endpoint} (plant {plant_uid})" if plant_uid else endpoint

        async with self.session.post(url, data=raw, headers=headers) as resp:
            if resp.status != 200:
                raise UpdateFailed(f"Failed to get {where}: HTTP {resp.status} from {url}")
            response_data = await self._read_json(resp, where)

        err_code = response_data.get("errCode", 0)
        _LOGGER.debug("%s: errCode=%s", where, err_code)
        if err_code != 0:
            raise UpdateFailed(
                f"Failed to get {where}: errCode {err_code}, {response_data.get('errMsg') or 'Unknown error'}"
            )
        return response_data

    async def _get_plant_list(self) -> dict[str, Any]:
        """Get list of plants."""
        return await self._post_v2("plant_list", {"pageNo": 1, "pageSize": 500})

    async def _get_plant_details_for_plant(self, plant_uid: str) -> dict[str, Any]:
        """Get plant details for specific plant."""
        return await self._post_v2("plant_detail", {"plantUid": plant_uid}, plant_uid)

    async def _get_device_list_for_plant(self, plant_uid: str) -> dict[str, Any]:
        """Get the plant inverters, in the shape of the old v1 device list.

        The plant device tree gives the inverters, the inverter energy detail
        their power and energy counters, the device capability their running
        state and the latest raw data record the yearly energy.
        """
        tree = await self._post_v2("device_tree", {"plantUid": plant_uid}, plant_uid)
        inverters = [d for d in tree.get("data") or [] if d.get("deviceType") == 1]

        devices = []
        for index, inverter in enumerate(inverters):
            device = {
                "deviceSn": inverter.get("deviceSn"),
                "deviceModel": inverter.get("deviceModel"),
                "firstOnlineTime": inverter.get("accessTime"),
            }
            # Sensors only read the first inverter, skip the extra requests for the rest
            if index == 0 and device["deviceSn"]:
                await self._add_inverter_data(plant_uid, device)
            devices.append(device)

        return {"data": {"list": devices}}

    async def _add_inverter_data(self, plant_uid: str, device: dict[str, Any]) -> None:
        """Add real time data to an inverter entry of the device list."""
        device_sn = device["deviceSn"]

        energy = (await self._post_v2("inverter_energy", {"deviceSn": device_sn}, plant_uid)).get("data") or {}
        for key in ("powerNow", "todayEnergy", "monthEnergy", "totalEnergy"):
            if energy.get(key) not in (None, ""):
                device[key] = energy[key]
        if energy.get("batterySoc") is not None:
            device["batEnergyPercent"] = energy["batterySoc"]

        capability = await self._optional(
            plant_uid, "inverter state", self._post_v2("device_capability", {"deviceSn": device_sn}, plant_uid)
        )
        if (capability.get("data") or {}).get("runningState") is not None:
            device["runningState"] = capability["data"]["runningState"]

        raw_data = await self._optional(plant_uid, "inverter raw data", self._get_latest_raw_data(device_sn, plant_uid))
        if raw_data.get("yearPVEnergy") is not None:
            device["yearEnergy"] = raw_data["yearPVEnergy"]

    async def _get_latest_raw_data(self, device_sn: str, plant_uid: str) -> dict[str, Any]:
        """Get the latest raw data record of an inverter."""
        today = datetime.now().strftime("%Y-%m-%d")
        response = await self._post_v2(
            "raw_data",
            {
                "deviceSn": device_sn,
                "deviceType": 1,
                "timeStr": today,
                "startTime": f"{today} 00:00:00",
                "endTime": f"{today} 23:59:59",
                "pageNo": 1,
                "pageSize": 1,
            },
            plant_uid,
        )
        records = (response.get("data") or {}).get("list") or []
        return records[0] if records else {}

    async def _get_v1(self, endpoint: str, params: dict[str, Any], plant_uid: str) -> dict[str, Any]:
        """GET a signed request to an api/v1 endpoint."""
        data = {
            **params,
            'appProjectName': 'elekeeper',
            'clientDate': datetime.now().strftime("%Y-%m-%d"),
            'lang': 'en',
            'timeStamp': int(time.time() * 1000),
            'random': generatkey(32),
            'clientId': 'esolar-monitor-admin',
        }
        url = f"{self.base_url}{ENDPOINTS[endpoint]}"
        where = f"{endpoint} (plant {plant_uid}, api v1)"

        async with self.session.get(
            url,
            params=calc_signature(data),
            headers={'Authorization': self.auth_token},
        ) as resp:
            if resp.status != 200:
                raise UpdateFailed(f"Failed to get {where}: HTTP {resp.status} from {url}")
            response_data = await self._read_json(resp, where)

        err_code = response_data.get("errCode", 0)
        _LOGGER.debug("%s: errCode=%s", where, err_code)
        if err_code != 0:
            raise UpdateFailed(f"Failed to get {where}: errCode {err_code}, {response_data.get('errMsg') or 'Unknown error'}")
        return response_data

    async def _get_battery_list_for_plant(self, plant_uid: str) -> dict[str, Any]:
        """Get battery list for specific plant.

        Still on v1: the v2 battery list lacks the per battery SOC,
        temperature and SOH the battery sensors read.
        """
        return await self._get_v1(
            "battery_list",
            {"plantUid": plant_uid, "pageSize": 100, "pageNo": 1, "searchOfficeIdArr": "1"},
            plant_uid,
        )

    async def _get_battery_info(self, device_sn: str, plant_uid: str) -> dict[str, Any]:
        """Get the inverter battery system info.

        Prefer v1, which still reports the remaining battery time
        (batteryWorkTime); fall back to the v2 equivalent, with the same
        fields, if v1 stops working.
        """
        try:
            return await self._get_v1("battery_info", {"deviceSn": device_sn}, plant_uid)
        except (UpdateFailed, aiohttp.ClientError) as err:
            self._warn_once(
                "battery_info_v1",
                "Falling back to api v2 for battery info, the remaining battery time will not be available: %s",
                err,
            )
            return await self._post_v2("battery_info", {"deviceSn": device_sn}, plant_uid)

    def _warn_once(self, key: str, msg: str, *args: Any) -> None:
        """Log a warning only the first time it happens for this coordinator."""
        if key in self._warned:
            _LOGGER.debug(msg, *args)
            return
        self._warned.add(key)
        _LOGGER.warning(msg, *args)

    async def _resolve_query_device(self, plant_uid: str) -> dict[str, Any]:
        """Resolve the device the plant home endpoints have to be queried with.

        The web client takes the first entry of the plant capability
        ``snList`` (inverter serial or EMS module serial, with its type).
        """
        capability = await self._post_v2("plant_capability", {"plantUid": plant_uid}, plant_uid)
        sn_list = (capability.get("data") or {}).get("snList") or []
        if not sn_list:
            _LOGGER.warning("Plant %s capability has no device serials, querying it by plant only", plant_uid)
            return {}
        return {"sn": sn_list[0].get("sn"), "snType": sn_list[0].get("snType")}

    async def _get_device_alarms(self, device_sn: str, plant_uid: str) -> dict[str, Any]:
        """Get the active alarms of a device."""
        return await self._post_v2(
            "device_alarms",
            {"deviceSn": device_sn, "alarmCommonState": 1, "pageNo": 1, "pageSize": 10},
            plant_uid,
        )
