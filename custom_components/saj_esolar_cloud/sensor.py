"""SAJ eSolar sensor platform."""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.util import dt as dt_util

from .const import DEVICE_INFO, DIRECTION_STATES, BATTERY_STATES, DOMAIN, H1_SENSORS
from .coordinator import RUNNING_STATE_ALARM, RUNNING_STATE_NORMAL, SAJeSolarDataUpdateCoordinator

# Device class mapping
DEVICE_CLASS_MAP = {
    "power": SensorDeviceClass.POWER,
    "energy": SensorDeviceClass.ENERGY,
    "battery": SensorDeviceClass.BATTERY,
    "timestamp": SensorDeviceClass.TIMESTAMP,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "voltage": SensorDeviceClass.VOLTAGE,
}

# State class mapping
STATE_CLASS_MAP = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
    "total": SensorStateClass.TOTAL,
}

def optional_float(data: dict[str, Any], key: str) -> float | None:
    """Read a numeric field, returning None (unknown) when it is missing."""
    value = data.get(key)
    if value in (None, ""):
        return None
    return float(str(value).rstrip("%"))

def is_running(running_state: Any) -> bool:
    """Whether an inverter runningState means it is online (normal or alarm)."""
    return int(running_state) in (RUNNING_STATE_NORMAL, RUNNING_STATE_ALARM)

def energy_stat(plant_stats: dict[str, Any], data_type: str, field: str) -> float:
    """Read a value from the plant statistics energyDataList.

    Entries are keyed by dataType (PV_ENERGY, LOAD_ENERGY, BUY_AND_SELL,
    CHARGE_AND_DISCHARGE). For the paired ones energy1 is buy/charge and
    energy2 is sell/discharge.
    """
    for entry in plant_stats.get("energyDataList") or []:
        if entry.get("dataType") == data_type:
            return float(entry.get(field) or 0)
    return 0

def environmental_stat(plant_stats: dict[str, Any], icon_key: str) -> float | None:
    """Read a value from the plant statistics environmentalInformation.

    Entries only carry a localized description, so match them by icon name
    (PLANT_CO2, PLANT_TREE, PLANT_COAL).
    """
    for entry in plant_stats.get("environmentalInformation") or []:
        if icon_key in (entry.get("iconUrl") or ""):
            return float(entry.get("value") or 0)
    return None

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAJ eSolar sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for first update to ensure we have plant data
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Create sensor entities for each monitored plant
    for plant_uid in coordinator.monitored_plants:
        # Get plant info for naming
        plant_data = coordinator.data.get(plant_uid, {})
        plant_info = plant_data.get("plant_info", {})
        plant_name = plant_info.get("plantName", plant_uid)

        # Create sensor entities for each defined H1 sensor for this plant
        for sensor_key, sensor_config in H1_SENSORS.items():
            entities.append(
                SAJeSolarSensor(
                    coordinator=coordinator,
                    sensor_key=sensor_key,
                    sensor_config=sensor_config,
                    plant_uid=plant_uid,
                    plant_name=plant_name,
                )
            )

        # Create individual battery devices and sensors
        battery_list = plant_data.get("battery_list", {}).get("data", {}).get("list", [])
        for i, battery in enumerate(battery_list):
            battery_sn = battery.get("batSn", f"battery_{i+1}")
            battery_name = f"{plant_name} Battery {i+1}"

            # Import BATTERY_SENSORS from const
            from .const import BATTERY_SENSORS

            # Create sensors for each battery
            for sensor_key, sensor_config in BATTERY_SENSORS.items():
                entities.append(
                    SAJeBatterySensor(
                        coordinator=coordinator,
                        sensor_key=sensor_key,
                        sensor_config=sensor_config,
                        plant_uid=plant_uid,
                        plant_name=plant_name,
                        battery_sn=battery_sn,
                        battery_name=battery_name,
                        battery_index=i,
                    )
                )

    async_add_entities(entities)

class SAJeSolarSensor(CoordinatorEntity[SAJeSolarDataUpdateCoordinator], SensorEntity):
    """Representation of a SAJ eSolar sensor."""

    def __init__(
        self,
        coordinator: SAJeSolarDataUpdateCoordinator,
        sensor_key: str,
        sensor_config: dict[str, Any],
        plant_uid: str,
        plant_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._sensor_key = sensor_key
        self._config = sensor_config
        self._plant_uid = plant_uid
        self._plant_name = plant_name

        # Set up entity properties with plant-specific naming
        self._attr_name = f"{plant_name} {sensor_config['name']}"
        self._attr_unique_id = f"{DOMAIN}_{plant_uid}_{sensor_key}"
        self._attr_icon = sensor_config["icon"]

        # Create plant-specific device info. Use the model reported by the
        # device list (e.g. R5-xxK-xxxx) when available, falling back to "H1".
        plant_data = coordinator.data.get(plant_uid, {})
        device_list = plant_data.get("device_list", {}).get("data", {}).get("list", [])
        device_data = device_list[0] if device_list else {}
        device_model = device_data.get("deviceModel") or "H1"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, plant_uid)},
            "name": plant_name,
            "manufacturer": "SAJ",
            "model": device_model,
        }

        # Set device class from mapping
        if sensor_config["device_class"]:
            self._attr_device_class = DEVICE_CLASS_MAP.get(sensor_config["device_class"])

        # Set state class from mapping
        if sensor_config["state_class"]:
            self._attr_state_class = STATE_CLASS_MAP.get(sensor_config["state_class"])

        # Set unit of measurement
        if sensor_config["unit"]:
            self._attr_native_unit_of_measurement = sensor_config["unit"]

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        try:
            # Get data for this specific plant
            plant_data = self.coordinator.data.get(self._plant_uid, {})

            # Get plant and device data from plant-specific structure
            plant_details = plant_data.get("plant_details", {}).get("data", {})
            device_list = plant_data.get("device_list", {}).get("data", {}).get("list", [])
            device_data = device_list[0] if device_list else {}

            # Get additional data sources for this plant
            plant_stats = plant_data.get("plant_statistics", {}).get("data", {})
            energy_flow = plant_data.get("energy_flow", {}).get("data", {})
            battery_info = plant_data.get("battery_info", {}).get("data", {})
            device_alarms = plant_data.get("device_alarms", {}).get("data", {})

            # Plant Detail Sensors - map from new plant data structure
            if self._sensor_key == "nowPower":
                return optional_float(device_data, "powerNow")
            elif self._sensor_key == "todayElectricity":
                return optional_float(device_data, "todayEnergy")
            elif self._sensor_key == "monthElectricity":
                return optional_float(device_data, "monthEnergy")
            elif self._sensor_key == "yearElectricity":
                return optional_float(device_data, "yearEnergy")
            elif self._sensor_key == "totalElectricity":
                return optional_float(device_data, "totalEnergy")
            elif self._sensor_key == "totalConsumpElec":
                # Use correct field names from plant statistics
                return energy_stat(plant_stats, "LOAD_ENERGY", "energy1Total")
            elif self._sensor_key == "totalBuyElec":
                return energy_stat(plant_stats, "BUY_AND_SELL", "energy1Total")
            elif self._sensor_key == "totalSellElec":
                return energy_stat(plant_stats, "BUY_AND_SELL", "energy2Total")
            elif self._sensor_key == "totalPlantTreeNum":
                return environmental_stat(plant_stats, "PLANT_TREE")
            elif self._sensor_key == "totalReduceCo2":
                return environmental_stat(plant_stats, "PLANT_CO2")
            elif self._sensor_key == "lastUploadTime":
                # Prefer the latest energy flow update time (real last update).
                # Fall back to the inverter's firstOnlineTime if it is missing.
                update_time = energy_flow.get("updateDate", "")
                if update_time:
                    try:
                        naive_dt = datetime.strptime(update_time, "%d/%m/%Y %H:%M:%S")
                        tz_name = plant_details.get("timeZone") or plant_details.get("timezone")
                        if tz_name:
                            try:
                                return dt_util.as_utc(naive_dt.replace(tzinfo=ZoneInfo(tz_name)))
                            except Exception:
                                pass
                        return dt_util.as_utc(naive_dt)
                    except ValueError:
                        pass

                # Fallback to original behaviour (first online time)
                timestamp = device_data.get("firstOnlineTime", "")
                if timestamp:
                    try:
                        naive_dt = datetime.strptime(timestamp, "%d/%m/%Y %H:%M:%S")
                        return dt_util.as_utc(naive_dt)
                    except ValueError:
                        return None
                return None
            elif self._sensor_key == "selfUseRate":
                # Calculate PV self-use rate from today's PV generation and grid
                # export. Prefer plant statistics, fall back to the inverter's
                # own today energy so it also works on H1 setups.
                today_pv_energy = energy_stat(plant_stats, "PV_ENERGY", "energy1Today")
                if today_pv_energy <= 0:
                    today_pv_energy = float(device_data.get("todayEnergy", 0) or 0)
                today_sell_energy = energy_stat(plant_stats, "BUY_AND_SELL", "energy2Today")

                if today_pv_energy > 0:
                    self_used_energy = max(today_pv_energy - today_sell_energy, 0)
                    return round((self_used_energy / today_pv_energy) * 100, 1)

                return 0

            # Device Power Sensors - map from energy flow and device data
            elif self._sensor_key == "pvPower":
                # Use device powerNow for real-time PV power (not solarPower which is capacity)
                return optional_float(device_data, "powerNow")
            elif self._sensor_key == "gridPower":
                # Grid power from energy flow - correct field name
                grid_power = float(energy_flow.get("sysGridPowerwatt", 0))
                grid_direction = energy_flow.get("gridDirection", 0)
                # Make negative when exporting
                return -grid_power if int(grid_direction) == 1 else grid_power
            elif self._sensor_key == "gridPowerAbsolute":
                return float(energy_flow.get("sysGridPowerwatt", 0))
            elif self._sensor_key == "batteryPower":
                # Battery power from energy flow - correct field name
                bat_power = float(energy_flow.get("batPower", 0))
                bat_direction = energy_flow.get("batteryDirection", 0)
                # Make negative when charging
                return -bat_power if int(bat_direction) == -1 else bat_power
            elif self._sensor_key == "batteryPowerAbsolute":
                return float(energy_flow.get("batPower", 0))
            elif self._sensor_key == "outPower":
                # Output power - house consumption from energy flow
                return float(energy_flow.get("totalLoadPowerwatt", 0))
            elif self._sensor_key == "totalLoadPower":
                # Total load power - correct field name
                return float(energy_flow.get("totalLoadPowerwatt", 0))
            elif self._sensor_key == "batCapcity":
                # Battery capacity from battery info (system total in kWh)
                return optional_float(battery_info, "batCapacity")
            elif self._sensor_key == "batCurr":
                # Battery current from battery info (system total)
                return optional_float(battery_info, "batCurrent")
            elif self._sensor_key == "batVoltage":
                # Battery voltage from battery info (system voltage)
                return optional_float(battery_info, "batVoltage")
            elif self._sensor_key == "usableBatCapacity":
                # Usable battery capacity from battery info
                return optional_float(battery_info, "usableBatCapacity")
            elif self._sensor_key == "batteryWorkTime":
                # Battery remaining time in hours (convert from minutes)
                work_time_min = optional_float(battery_info, "batteryWorkTime")
                if work_time_min is None:
                    return None
                return round(work_time_min / 60, 1)  # Convert to hours
            elif self._sensor_key == "operatingMode":
                # Operating mode from battery info
                return battery_info.get("userModeName") or energy_flow.get("userModeName") or "Unknown"
            elif self._sensor_key == "batEnergyPercent":
                return optional_float(device_data, "batEnergyPercent")
            elif self._sensor_key == "batteryDirection":
                direction = energy_flow.get("batteryDirection", 0)
                return BATTERY_STATES.get(int(direction), f"Unknown ({direction})")
            elif self._sensor_key == "isOnline":
                running_state = device_data.get("runningState")
                if running_state is None:
                    return None
                return "Yes" if is_running(running_state) else "No"
            elif self._sensor_key == "inverterStatus":
                # Inverter status based on the active alarms of the device
                # (plant statistics no longer report a deviceStatus)
                if device_alarms.get("list") or device_data.get("runningState") == RUNNING_STATE_ALARM:
                    return "Alarm"
                if "list" not in device_alarms:
                    # Alarms could not be fetched
                    return None
                return "OK"

            # Daily Values from plant statistics and device data - correct field names
            elif self._sensor_key == "dailyConsumption":
                return energy_stat(plant_stats, "LOAD_ENERGY", "energy1Today")
            elif self._sensor_key == "dailyGridImport":
                return energy_stat(plant_stats, "BUY_AND_SELL", "energy1Today")
            elif self._sensor_key == "dailyGridExport":
                return energy_stat(plant_stats, "BUY_AND_SELL", "energy2Today")
            elif self._sensor_key == "dailyBatteryCharge":
                return energy_stat(plant_stats, "CHARGE_AND_DISCHARGE", "energy1Today")
            elif self._sensor_key == "dailyBatteryDischarge":
                return energy_stat(plant_stats, "CHARGE_AND_DISCHARGE", "energy2Today")
            elif self._sensor_key == "dailyTreesPlanted":
                # No longer provided by the plant statistics endpoint
                return None
            elif self._sensor_key == "dailyReduceCo2":
                # No longer provided by the plant statistics endpoint
                return None

            # Direction sensors from energy flow
            elif self._sensor_key == "pvDirection":
                value = int(energy_flow.get("pvDirection", 0))
                return DIRECTION_STATES.get(value, f"Unknown ({value})")
            elif self._sensor_key == "gridDirection":
                value = int(energy_flow.get("gridDirection", 0))
                return DIRECTION_STATES.get(value, f"Unknown ({value})")
            elif self._sensor_key == "outPutDirection":
                value = int(energy_flow.get("outputDirection", 0))
                return DIRECTION_STATES.get(value, f"Unknown ({value})")

            # Battery Info from battery list
            elif self._sensor_key in ["batVoltage", "batTemperature"]:
                battery_list = plant_data.get("battery_list", {}).get("data", {}).get("list", [])
                if battery_list:
                    battery = battery_list[0]  # Use first battery for now
                    if self._sensor_key == "batTemperature":
                        temp_str = battery.get("batTemperature", "0℃")
                        return float(temp_str.rstrip("℃"))
                return 0

            # For sensors we haven't mapped yet, return 0 or appropriate default
            return 0

        except (KeyError, TypeError, ValueError) as e:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes for main plant sensors."""
        if self._sensor_key == "operatingMode":
            try:
                # Get data for this specific plant
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})

                # Add system-level attributes to operating mode sensor
                attributes = {}

                battery_quantity = battery_info.get("batteryQuantity")
                if battery_quantity:
                    attributes["battery_quantity"] = battery_quantity

                update_date = battery_info.get("updateDate")
                if update_date:
                    attributes["last_update"] = update_date

                return attributes if attributes else None

            except (KeyError, TypeError, ValueError):
                pass

        elif self._sensor_key == "inverterStatus":
            try:
                # Get data for this specific plant
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                device_alarms = plant_data.get("device_alarms", {}).get("data", {})

                attributes = {}

                alarm_list = device_alarms.get("list", [])
                if alarm_list:
                    # Get the first (most recent) alarm
                    alarm = alarm_list[0]
                    attributes["alarm_name"] = alarm.get("alarmName", "Unknown")
                    attributes["alarm_level"] = alarm.get("alarmLevelName", "Unknown")
                    attributes["alarm_duration"] = alarm.get("alarmDuration", "Unknown")
                    attributes["alarm_start_time"] = alarm.get("alarmStartTime", "Unknown")
                    attributes["alarm_state"] = alarm.get("alarmStateName", "Unknown")

                return attributes if attributes else None

            except (KeyError, TypeError, ValueError):
                pass

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if self.coordinator.data is None:
            return False

        try:
            # Check if device is online using plant-specific data structure
            plant_data = self.coordinator.data.get(self._plant_uid, {})
            device_list = plant_data.get("device_list", {}).get("data", {}).get("list", [])
            if device_list:
                device_data = device_list[0]
                # Unknown state (e.g. the request failed) keeps the entity available
                running_state = device_data.get("runningState")
                return running_state is None or bool(int(running_state))
            return False
        except (KeyError, TypeError, ValueError):
            return False


class SAJeBatterySensor(CoordinatorEntity[SAJeSolarDataUpdateCoordinator], SensorEntity):
    """Representation of a SAJ eSolar battery sensor."""

    def __init__(
        self,
        coordinator: SAJeSolarDataUpdateCoordinator,
        sensor_key: str,
        sensor_config: dict[str, Any],
        plant_uid: str,
        plant_name: str,
        battery_sn: str,
        battery_name: str,
        battery_index: int,
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator)

        self._sensor_key = sensor_key
        self._config = sensor_config
        self._plant_uid = plant_uid
        self._plant_name = plant_name
        self._battery_sn = battery_sn
        self._battery_name = battery_name
        self._battery_index = battery_index

        # Set up entity properties with battery-specific naming
        self._attr_name = f"{battery_name} {sensor_config['name']}"
        self._attr_unique_id = f"{DOMAIN}_{plant_uid}_{battery_sn}_{sensor_key}"
        self._attr_icon = sensor_config["icon"]

        # Create battery-specific device info
        # Get battery model from coordinator data
        plant_data = coordinator.data.get(plant_uid, {})
        battery_list = plant_data.get("battery_list", {}).get("data", {}).get("list", [])
        battery_model = "Unknown"
        if battery_index < len(battery_list):
            battery_model = battery_list[battery_index].get("batModel", "Unknown")

        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{plant_uid}_{battery_sn}")},
            "name": battery_name,
            "manufacturer": "SAJ",
            "model": battery_model,
            "via_device": (DOMAIN, plant_uid),
        }

        # Set device class from mapping
        if sensor_config["device_class"]:
            self._attr_device_class = DEVICE_CLASS_MAP.get(sensor_config["device_class"])

        # Set state class from mapping
        if sensor_config["state_class"]:
            self._attr_state_class = STATE_CLASS_MAP.get(sensor_config["state_class"])

        # Set unit of measurement
        if sensor_config["unit"]:
            self._attr_native_unit_of_measurement = sensor_config["unit"]

    @property
    def native_value(self) -> StateType:
        """Return the battery sensor value."""
        try:
            # Get data for this specific plant
            plant_data = self.coordinator.data.get(self._plant_uid, {})
            battery_list = plant_data.get("battery_list", {}).get("data", {}).get("list", [])

            # Get this specific battery data
            if self._battery_index < len(battery_list):
                battery_data = battery_list[self._battery_index]
            else:
                return None

            # Map battery sensor values
            if self._sensor_key == "batSoc":
                soc_str = battery_data.get("batSoc", "0%")
                return float(soc_str.rstrip("%"))
            elif self._sensor_key == "batTemperature":
                temp_str = battery_data.get("batTemperature", "0℃")
                return float(temp_str.rstrip("℃"))
            elif self._sensor_key == "batSoh":
                soh_raw = battery_data.get("batSoh", "0")
                try:
                    # Try interpreting as degradation percentage (1% degraded = 99% health)
                    degradation = float(soh_raw)
                    health = 100 - degradation
                    return max(0, min(100, health))  # Clamp between 0-100%
                except (ValueError, TypeError):
                    return 0
            elif self._sensor_key == "runningState":
                state = battery_data.get("runningState", 0)
                state_map = {0: "Offline", 1: "Standby", 2: "Running"}
                return state_map.get(int(state), f"Unknown ({state})")
            elif self._sensor_key == "batModel":
                return battery_data.get("batModel", "Unknown")
            elif self._sensor_key == "batPower":
                # Individual battery power - need to calculate from system data
                # For now, use system power divided by number of batteries
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                system_power = float(battery_info.get("batPower", 0))
                battery_quantity = battery_info.get("batteryQuantity", 2)
                return round(system_power / max(1, battery_quantity), 1)
            elif self._sensor_key == "batCurrent":
                # Individual battery current - use system current divided by batteries
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                system_current = float(battery_info.get("batCurrent", 0))
                battery_quantity = battery_info.get("batteryQuantity", 2)
                return round(system_current / max(1, battery_quantity), 2)
            elif self._sensor_key == "batVoltage":
                # Individual battery voltage - use system voltage (same for all)
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                return float(battery_info.get("batVoltage", 0))
            elif self._sensor_key == "todayBatCharge":
                # Today battery charge - use system value divided by batteries
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                system_charge = float(battery_info.get("todayBatChgEnergy", 0))
                battery_quantity = battery_info.get("batteryQuantity", 2)
                return round(system_charge / max(1, battery_quantity), 2)
            elif self._sensor_key == "todayBatDischarge":
                # Today battery discharge - use system value divided by batteries
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                system_discharge = float(battery_info.get("todayBatDisEnergy", 0))
                battery_quantity = battery_info.get("batteryQuantity", 2)
                return round(system_discharge / max(1, battery_quantity), 2)
            elif self._sensor_key == "totalBatCharge":
                # Total battery charge - use system value divided by batteries
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                system_charge = float(battery_info.get("totalBatChgEnergy", 0))
                battery_quantity = battery_info.get("batteryQuantity", 2)
                return round(system_charge / max(1, battery_quantity), 2)
            elif self._sensor_key == "totalBatDischarge":
                # Total battery discharge - use system value divided by batteries
                plant_data = self.coordinator.data.get(self._plant_uid, {})
                battery_info = plant_data.get("battery_info", {}).get("data", {})
                system_discharge = float(battery_info.get("totalBatDisEnergy", 0))
                battery_quantity = battery_info.get("batteryQuantity", 2)
                return round(system_discharge / max(1, battery_quantity), 2)

            return None

        except (KeyError, TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes for battery sensors."""
        if self._sensor_key != "batModel":
            return None

        try:
            # Get data for this specific plant
            plant_data = self.coordinator.data.get(self._plant_uid, {})
            battery_list = plant_data.get("battery_list", {}).get("data", {}).get("list", [])

            # Get this specific battery data
            if self._battery_index < len(battery_list):
                battery_data = battery_list[self._battery_index]

                # Add hardware and software versions as attributes to battery model sensor
                attributes = {}

                hw_version = battery_data.get("bmsHardwareVersion")
                if hw_version:
                    attributes["hardware_version"] = hw_version

                sw_version = battery_data.get("bmsSoftwareVersion")
                if sw_version:
                    attributes["software_version"] = sw_version

                # Add other useful battery info
                battery_sn = battery_data.get("batSn")
                if battery_sn:
                    attributes["serial_number"] = battery_sn

                cluster_id = battery_data.get("clusterId")
                if cluster_id:
                    attributes["cluster_id"] = cluster_id

                return attributes if attributes else None

        except (KeyError, TypeError, ValueError):
            pass

        return None

    @property
    def available(self) -> bool:
        """Return if battery entity is available."""
        if self.coordinator.data is None:
            return False

        try:
            # Check if battery data is available
            plant_data = self.coordinator.data.get(self._plant_uid, {})
            battery_list = plant_data.get("battery_list", {}).get("data", {}).get("list", [])
            return self._battery_index < len(battery_list)
        except (KeyError, TypeError, ValueError):
            return False
