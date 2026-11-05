#  Copyright (c) 2021-2025, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The Narodmon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SHOW_ON_MAP,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import NarodmonApiClient, NarodmonApiError, NarodmonUnauthorizedError
from .const import (
    CONF_APIKEY,
    CONF_CENTER_HOME,
    CONF_SCAN_INTERVAL,
    CONF_SEARCH_AREA_RADIUS,
    CONF_SERVER,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SEARCH_AREA_RADIUS,
    DEFAULT_SERVER,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    SERVERS,
)

STEP_USER_DATA_SCHEMA: vol.Schema = vol.Schema(
    {
        vol.Required(CONF_SERVER, default=DEFAULT_SERVER): vol.In(
            {srv_id: srv["title"] for srv_id, srv in SERVERS.items()}
        ),
        vol.Required(CONF_APIKEY): cv.string,
        vol.Optional(CONF_CENTER_HOME, default=True): bool,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    }
)

STEP_OPTIONS_SCHEMA: vol.Schema = vol.Schema(
    {
        vol.Required(CONF_CENTER_HOME, default=True): bool,
        vol.Required(CONF_SHOW_ON_MAP, default=False): bool,
        vol.Optional(CONF_LATITUDE, default=None, required=False): vol.Coerce(float),
        vol.Optional(CONF_LONGITUDE, default=None, required=False): vol.Coerce(float),
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
        vol.Required(
            CONF_SEARCH_AREA_RADIUS, default=DEFAULT_SEARCH_AREA_RADIUS
        ): cv.positive_float,
    }
)


class NarodmonFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Narodmon."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._errors: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            valid = await self._test_credentials(user_input)
            if valid:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=SERVERS[user_input[CONF_SERVER]]["title"],
                    data=user_input,
                )

            self._errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=self._errors,
        )

    async def _test_credentials(self, user_input: dict[str, str]) -> bool:
        """Return true if credentials is valid."""
        try:
            client = NarodmonApiClient(
                self.hass,
                apikey=user_input[CONF_APIKEY],
                verify_ssl=user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                timeout=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                server=user_input.get(CONF_SERVER, DEFAULT_SERVER),
            )
            await client.async_init()
        except NarodmonUnauthorizedError:
            self._errors["base"] = "auth"
            return False
        except NarodmonApiError:
            self._errors["base"] = "api_error"
            return False
        except Exception:  # pylint: disable=broad-except
            self._errors["base"] = "unknown"
            return False

        return True


class NarodmonOptionsFlowHandler(OptionsFlow):
    """Narodmon config flow options handler."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Narodmon options flow."""
        super().__init__()
        self._options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            self._options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_OPTIONS_SCHEMA,
        )

    async def _update_options(self) -> FlowResult:
        """Update config entry options."""
        scan_interval = self._options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        self._options[CONF_SCAN_INTERVAL] = (
            scan_interval.total_seconds()
            if hasattr(scan_interval, "total_seconds")
            else scan_interval
        )
        return self.async_create_entry(title="", data=self._options)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get component options flow."""
        return NarodmonOptionsFlowHandler(config_entry)
