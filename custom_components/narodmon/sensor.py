#  Copyright (c) 2021-2024, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The NarodMon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""

import logging
import time

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_ID,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import YAML_DOMAIN, NarodmonDataUpdateCoordinator
from .const import (
    ATTR_DEVICE_NAME,
    ATTR_DISTANCE,
    ATTR_LAT,
    ATTR_LON,
    ATTR_SENSOR_ID,
    ATTR_SENSOR_NAME,
    ATTRIBUTION,
    CONF_SHOW_ON_MAP,
    DOMAIN,
    FRESHNESS_TIME,
    NAME,
    SENSOR_TYPES,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Set up sensor platform."""
    if entry.source == "import":
        config = hass.data[YAML_DOMAIN]
        for index, device_config in enumerate(config.get("devices")):
            vdev_id = "-".join([entry.entry_id, str(index)])
            coordinator = hass.data[DOMAIN][entry.entry_id][index]
            name = device_config.get(CONF_NAME, hass.config.location_name)
            types = device_config.get("sensors", SENSOR_TYPES.keys())

            sensors = []
            for stype in types:
                entity_name = " ".join([name, SENSOR_TYPES[stype]["name"]])
                sensors.append(
                    NarodmonSensor(
                        coordinator,
                        stype,
                        vdev_id,
                        entity_name,
                    )
                )
            if sensors:
                async_add_devices(sensors)

    else:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        # Build a virtual device config from entry options
        device_config = {
            "name": hass.config.location_name,
            CONF_SHOW_ON_MAP: entry.options.get(CONF_SHOW_ON_MAP, False),
            "scan_interval": entry.options.get("scan_interval", 180),
            "search_area_radius": entry.options.get("search_area_radius", 10),
        }
        coordinator.latitude = hass.config.latitude
        coordinator.longitude = hass.config.longitude
        coordinator.show_on_map = entry.options.get(CONF_SHOW_ON_MAP, False)
        coordinator.max_distance = entry.options.get("search_area_radius", 10)

        for stype in SENSOR_TYPES:
            entity_name = f"{hass.config.location_name} {SENSOR_TYPES[stype]['name']}"
            async_add_devices(
                NarodmonSensor(
                    coordinator,
                    stype,
                    entry.entry_id,
                    entity_name,
                )
            )


class NarodmonSensor(CoordinatorEntity, SensorEntity):
    """Implementation of an NarodMon sensor."""

    def __init__(
        self,
        coordinator: NarodmonDataUpdateCoordinator,
        sensor_type: str,
        device_id: str,
        name: str,
    ) -> None:
        """Class initialization."""
        super().__init__(coordinator)

        self._sensor_type_id = SENSOR_TYPES[sensor_type]["id"]
        self._sensor_id = None

        self._attr_unique_id = f"{device_id}-{sensor_type}"
        self._attr_name = name
        self._attr_icon = SENSOR_TYPES[sensor_type].get("icon")
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type].get(
            "unit_of_measurement"
        )
        self._attr_device_class = SENSOR_TYPES[sensor_type].get("device_class")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": NAME,
            "model": VERSION,
        }

    def _update_state(self) -> None:
        """Update entity state."""
        fresh = int(time.time() - FRESHNESS_TIME)
        show_on_map = self.coordinator.show_on_map
        for sensor in self.coordinator.data:
            if sensor["type"] == self._sensor_type_id and sensor["time"] >= fresh:
                if self._attr_native_value == sensor["value"]:
                    return

                device = sensor["device"]

                self._attr_native_value = sensor["value"]

                if self._sensor_id != int(sensor["id"]):
                    self._sensor_id = int(sensor["id"])
                    self._attr_extra_state_attributes = {
                        ATTR_ATTRIBUTION: ATTRIBUTION,
                    }

                self._attr_extra_state_attributes[ATTR_SENSOR_ID] = "S" + str(
                    self._sensor_id
                )
                self._attr_extra_state_attributes[ATTR_SENSOR_NAME] = sensor["name"]
                self._attr_extra_state_attributes[ATTR_DEVICE_ID] = "D" + str(
                    device["id"]
                )
                self._attr_extra_state_attributes[ATTR_DEVICE_NAME] = device["name"]
                self._attr_extra_state_attributes[ATTR_DISTANCE] = device["distance"]
                if "location" in device:
                    self._attr_extra_state_attributes["location"] = device["location"]
                if "lat" in device and "lon" in device:
                    if show_on_map:
                        self._attr_extra_state_attributes["latitude"] = device["lat"]
                        self._attr_extra_state_attributes["longitude"] = device["lon"]
                    else:
                        self._attr_extra_state_attributes[ATTR_LAT] = device["lat"]
                        self._attr_extra_state_attributes[ATTR_LON] = device["lon"]

                _LOGGER.debug(
                    "Set sensor '%s' state to %s %s",
                    self._attr_name,
                    self._attr_native_value,
                    self._attr_native_unit_of_measurement,
                )
                return

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state()
        super()._handle_coordinator_update()

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        self._update_state()
        return super().native_value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        fresh = int(time.time() - FRESHNESS_TIME)
        for sensor in self.coordinator.data:
            if sensor["type"] == self._sensor_type_id and sensor["time"] >= fresh:
                return True

        return False
