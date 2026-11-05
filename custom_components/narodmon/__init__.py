#  Copyright (c) 2021-2025, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The NarodMon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""

import asyncio
import logging
import time
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import (
    CONF_DEVICES,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_ON_MAP,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NARODMON_IDS, NarodmonApiClient, NarodmonUnauthorizedError
from .const import (
    CONF_APIKEY,
    CONF_CENTER_HOME,
    CONF_SEARCH_AREA_RADIUS,
    CONF_SERVER,
    CONF_SHOW_ON_MAP,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SEARCH_AREA_RADIUS,
    DEFAULT_SERVER,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    FRESHNESS_TIME,
    SENSOR_TYPES,
    STARTUP_MESSAGE,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

YAML_DOMAIN = f"_yaml_{DOMAIN}"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up this integration using YAML."""
    if DOMAIN not in config:
        return True

    hass.data[YAML_DOMAIN] = config[DOMAIN]
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data={}
        )
    )

    legacy_uuid_fpath = Path(hass.config.path("storage", DOMAIN + ".uuid"))
    if legacy_uuid_fpath.exists():
        await hass.async_add_executor_job(legacy_uuid_fpath.unlink)
        _LOGGER.debug("Legacy UUID file removed (%s).", legacy_uuid_fpath)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    if entry.source == "import":
        if YAML_DOMAIN not in hass.data:
            await hass.config_entries.async_remove(entry.entry_id)
            raise ConfigEntryNotReady

        config = hass.data[YAML_DOMAIN]

        apikey = config.get(CONF_APIKEY)
        if apikey is not None:
            _LOGGER.warning(
                "Field '%s' is NOT recommended to use. If you don't have your own "
                "API key with special limits please remove it from your configs.",
                CONF_APIKEY,
            )

        client = NarodmonApiClient(
            hass,
            apikey=apikey,
            verify_ssl=config.get(CONF_VERIFY_SSL),
            timeout=config.get(CONF_TIMEOUT),
        )

        for index, device_config in enumerate(config.get(CONF_DEVICES)):
            coordinator = NarodmonDataUpdateCoordinator(hass, client, device_config)
            await coordinator.async_refresh()

            if not coordinator.last_update_success:
                raise ConfigEntryNotReady

            hass.data[DOMAIN].setdefault(entry.entry_id, {})
            hass.data[DOMAIN][entry.entry_id][index] = coordinator

        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    else:
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(entry.entry_id)

        options = entry.options
        center_home = options.get(CONF_CENTER_HOME, True)
        latitude = (
            hass.config.latitude
            if center_home
            else options.get(CONF_LATITUDE, hass.config.latitude)
        )
        longitude = (
            hass.config.longitude
            if center_home
            else options.get(CONF_LONGITUDE, hass.config.longitude)
        )

        apikey = entry.data.get(CONF_APIKEY)
        server = entry.data.get(CONF_SERVER, DEFAULT_SERVER)
        verify_ssl = entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        client = NarodmonApiClient(
            hass,
            apikey=apikey,
            verify_ssl=verify_ssl,
            timeout=timeout,
            server=server,
        )

        coordinator_config = {
            "latitude": latitude,
            "longitude": longitude,
            CONF_SHOW_ON_MAP: options.get(CONF_SHOW_ON_MAP, False),
            CONF_SCAN_INTERVAL: timedelta(
                seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            )
            if isinstance(options.get(CONF_SCAN_INTERVAL), int)
            else options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            CONF_SEARCH_AREA_RADIUS: options.get(
                CONF_SEARCH_AREA_RADIUS, DEFAULT_SEARCH_AREA_RADIUS
            ),
        }

        coordinator = NarodmonDataUpdateCoordinator(hass, client, coordinator_config)
        await coordinator.async_refresh()

        if not coordinator.last_update_success:
            raise ConfigEntryNotReady

        hass.data[DOMAIN][entry.entry_id] = coordinator

        if entry.entry_id not in hass.data[DOMAIN].get("sensor_setup", {}):
            await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
            hass.data[DOMAIN].setdefault("sensor_setup", {})[entry.entry_id] = True

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if entry.source == "import":
        unloaded = all(
            await asyncio.gather(
                *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
            )
        )
        if unloaded:
            hass.data[DOMAIN].pop(entry.entry_id, None)
        return unloaded

    hass.data[DOMAIN].pop(entry.entry_id, None)
    hass.data[DOMAIN].get("sensor_setup", {}).pop(entry.entry_id, None)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class NarodmonDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Narodmon Cloud."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: NarodmonApiClient,
        config: dict,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=config.get(CONF_SCAN_INTERVAL)
        )

        self.api = client
        self.latitude = config.get("latitude", hass.config.latitude)
        self.longitude = config.get("longitude", hass.config.longitude)
        self.show_on_map = config.get(CONF_SHOW_ON_MAP, False)
        self.max_distance = config.get(
            CONF_SEARCH_AREA_RADIUS, DEFAULT_SEARCH_AREA_RADIUS
        )
        self.types = SENSOR_TYPES.keys()
        self.devices: NARODMON_IDS = set()
        self.sensors: NARODMON_IDS = set()

        self._first_run = True

    async def _async_update_data(self) -> list:
        """Update data via library."""
        fresh = int(time.time() - FRESHNESS_TIME)
        sensors: list = []

        for _ in range(2):
            try:
                data = await self.api.async_update_data(no_throttle=self._first_run)
            except NarodmonUnauthorizedError:
                _LOGGER.warning("Request failed: Need reauthorization.")
                continue

            if data is None:
                raise UpdateFailed

            tps: NARODMON_IDS = {SENSOR_TYPES[i].get("id") for i in self.types}
            for sensor in data.values():
                if sensor["id"] in self.sensors and sensor["time"] >= fresh:
                    sensors.append(sensor)
                    tps.discard(sensor["type"])

            if tps:
                async def async_nearby_listener(
                    new_sensors: dict,
                ) -> None:
                    self.devices = self.devices.union(new_sensors.values())
                    self.sensors = self.sensors.union(new_sensors.keys())

                await self.api.async_set_nearby_listener(
                    async_nearby_listener,
                    self.latitude,
                    self.longitude,
                    self.max_distance,
                    tps,
                )

            if not self._first_run or self.api.devices:
                break

        self._first_run = False

        return sensors
