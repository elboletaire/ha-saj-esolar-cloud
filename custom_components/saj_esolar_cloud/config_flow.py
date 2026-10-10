"""Config flow for SAJ eSolar integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, CONF_REGION, CONF_MONITORED_PLANTS, REGIONS
from .coordinator import SAJeSolarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION, default="eu"): vol.In(list(REGIONS.keys())),
    }
)

class SAJeSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAJ eSolar."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._username = None
        self._password = None
        self._region = None
        self._plants = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store credentials for next step
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._region = user_input[CONF_REGION]

            # Test authentication and get plant list
            session = async_create_clientsession(self.hass)
            coordinator = SAJeSolarDataUpdateCoordinator(
                self.hass,
                session,
                self._username,
                self._password,
                self._region,
            )

            try:
                await coordinator._authenticate()
                plant_data = await coordinator._get_plant_list()

                if plant_data.get("data", {}).get("list"):
                    self._plants = plant_data["data"]["list"]
                    return await self.async_step_plant_selection()
                else:
                    errors["base"] = "no_plants"
            except ConfigEntryAuthFailed as err:
                _LOGGER.warning("SAJ login failed: %s", err)
                errors["base"] = "invalid_auth"
            except UpdateFailed as err:
                _LOGGER.error("Could not connect to the SAJ API: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error setting up SAJ eSolar Cloud")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_plant_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle plant selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_plants = user_input[CONF_MONITORED_PLANTS]
            if not selected_plants:
                errors["base"] = "no_plants_selected"
            else:
                # Create final config data
                config_data = {
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_REGION: self._region,
                    CONF_MONITORED_PLANTS: selected_plants,
                }

                await self.async_set_unique_id(self._username)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SAJ eSolar ({self._username})",
                    data=config_data,
                )

        # Create plant selection schema
        plant_options = {}
        if self._plants:
            for plant in self._plants:
                plant_name = plant["plantName"]
                plant_uid = plant["plantUid"]
                plant_options[plant_uid] = plant_name

        plant_schema = vol.Schema({
            vol.Required(CONF_MONITORED_PLANTS): cv.multi_select(plant_options),
        })

        return self.async_show_form(
            step_id="plant_selection",
            data_schema=plant_schema,
            errors=errors,
            description_placeholders={
                "plant_count": str(len(self._plants) if self._plants else 0)
            }
        )
