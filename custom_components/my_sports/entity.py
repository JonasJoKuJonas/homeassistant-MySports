"""MySports base entity."""

from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MySportsCoordinator


class MySportsCoordinatorEntity(CoordinatorEntity[MySportsCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: MySportsCoordinator, studio_id: int, studio_name: str
    ) -> None:
        super().__init__(coordinator)
        self.studio_id = studio_id
        self.studio_name = studio_name

        stable_id = coordinator.config_entry.data.get(CONF_USERNAME)
        self._attr_unique_id = f"{stable_id}_{studio_id}"
        self._attr_translation_key = "studio_utilization"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{stable_id}_{studio_id}")},
            configuration_url="https://www.mysports.com",
            manufacturer="MySports",
            model="Studio",
            name=studio_name,
            serial_number=str(studio_id),
        )

    @property
    def entity_picture(self) -> str | None:
        logo_url = self.coordinator.get_studio_logo_url(self.studio_id)
        return logo_url if logo_url else None

    @property
    def native_value(self):
        studio_data = self.coordinator.get_studio_data(self.studio_id)
        if not studio_data or not studio_data.get("available", False):
            return None
        return studio_data.get("active_checkins")

    @property
    def available(self):
        studio_data = self.coordinator.get_studio_data(self.studio_id)
        return studio_data.get("available", False) if studio_data else False

    @property
    def extra_state_attributes(self):
        studio_data = self.coordinator.get_studio_data(self.studio_id)
        if not studio_data:
            return {}
        return {
            "studio_id": studio_data.get("id"),
            "studio_name": studio_data.get("name"),
            "primary_studio": studio_data.get("primary", False),
            "logo_url": studio_data.get("logo_url"),
            "last_update": self.coordinator.data.get("last_update"),
            "authenticated": self.coordinator.data.get("authenticated", False),
            **({"error": studio_data["error"]} if "error" in studio_data else {}),
        }
