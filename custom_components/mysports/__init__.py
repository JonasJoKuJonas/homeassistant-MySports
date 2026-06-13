"""MySports Integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import MySportsCoordinator, MySportsCoursesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MySports from a config entry."""
    coordinator = MySportsCoordinator(hass, entry)
    entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()

    # Create courses coordinator after studios are loaded
    courses_coordinator = MySportsCoursesCoordinator(
        hass, entry, coordinator.api, coordinator.get_all_studios()
    )
    await courses_coordinator.async_config_entry_first_refresh()

    entry.runtime_data.courses_coordinator = courses_coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: MySportsCoordinator = entry.runtime_data
    coordinator.update_interval_from_options()
    # Update courses interval if available
    if hasattr(coordinator, "courses_coordinator"):
        new_course_interval = entry.options.get("calendar_scan_interval", 60)
        coordinator.courses_coordinator.update_interval = timedelta(
            minutes=new_course_interval
        )
        coordinator.courses_coordinator._schedule_refresh()
