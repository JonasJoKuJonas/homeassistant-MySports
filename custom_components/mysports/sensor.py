"""MySports sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MySportsCoordinator
from .entity import MySportsCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MySportsCoordinator = entry.runtime_data

    studios = coordinator.get_all_studios()
    if not studios:
        _LOGGER.warning("No studios found for MySports integration")
        return

    entities = [
        MySportsUtilizationSensor(
            coordinator, studio["id"], studio["name"], studio.get("primary", False)
        )
        for studio in studios
    ]
    async_add_entities(entities)
    _LOGGER.info("Added %d MySports studio sensors", len(entities))


class MySportsUtilizationSensor(MySportsCoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: MySportsCoordinator,
        studio_id: int,
        studio_name: str,
        is_primary: bool = False,
    ):
        super().__init__(coordinator, studio_id, studio_name)
        self.is_primary = is_primary
        self._attr_icon = "mdi:fitness"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_translation_key = "studio_utilization"
        self._attr_suggested_display_precision = 0
        self._attr_name = None

    @property
    def native_value(self):
        studio_data = self.coordinator.get_studio_data(self.studio_id)
        if not studio_data or not studio_data.get("available", False):
            return None
        count = studio_data.get("active_checkins")
        return int(count) if count is not None else None

    @property
    def extra_state_attributes(self):
        studio_data = self.coordinator.get_studio_data(self.studio_id)
        if not studio_data:
            return {
                "studio_id": self.studio_id,
                "studio_name": self.studio_name,
                "primary": self.is_primary,
            }
        return {
            "studio_id": studio_data.get("id"),
            "studio_name": studio_data.get("name"),
            "primary": studio_data.get("primary", False),
            "last_update": self.coordinator.data.get("last_update"),
            "authenticated": self.coordinator.data.get("authenticated", False),
            **({"error": studio_data["error"]} if "error" in studio_data else {}),
        }

    @property
    def available(self):
        studio_data = self.coordinator.get_studio_data(self.studio_id)
        return studio_data.get("active_checkins") is not None if studio_data else False
