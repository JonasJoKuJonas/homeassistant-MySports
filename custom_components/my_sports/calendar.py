"""Calendar platform for MySports courses."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import MySportsCoursesCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    coordinator: MySportsCoursesCoordinator = entry.runtime_data.courses_coordinator

    # Erstelle eine Kalender-Entität pro Studio
    entities = []
    for studio in coordinator.studios:
        studio_id = studio.get("id")
        studio_name = studio.get("name")
        if studio_id and studio_name:
            entities.append(
                MySportsCourseCalendar(
                    coordinator,
                    entry,
                    studio_id,
                    studio_name,
                    studio.get("primary", False),
                )
            )

    async_add_entities(entities)
    _LOGGER.info("Added %d MySports course calendars", len(entities))


class MySportsCourseCalendar(
    CoordinatorEntity[MySportsCoursesCoordinator], CalendarEntity
):
    """Calendar entity for MySports courses per studio."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar"

    def __init__(
        self,
        coordinator: MySportsCoursesCoordinator,
        entry: ConfigEntry,
        studio_id: int,
        studio_name: str,
        is_primary: bool = False,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._entry = entry
        self._studio_id = studio_id
        self._studio_name = studio_name
        self._is_primary = is_primary

        stable_id = entry.data.get("username")
        self._attr_unique_id = f"{stable_id}_{studio_id}_courses"
        self._attr_name = None
        self._attr_translation_key = "courses_calendar"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{stable_id}_{studio_id}")},
            "configuration_url": "https://www.mysports.com",
            "manufacturer": "MySports",
            "model": "Studio",
            "name": studio_name,
            "serial_number": str(studio_id),
        }

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event for this studio."""
        events = self._get_events(dt_util.now(), dt_util.now() + timedelta(days=365))
        return events[0] if events else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events(start_date, end_date)

    def _get_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events between start_date and end_date from cached data."""
        courses = self.coordinator.get_all_courses()
        events: List[CalendarEvent] = []

        for course in courses:
            # Prüfe ob dieser Kurs zum Studio gehört
            slots = course.get("slots", [])
            course_belongs_to_studio = False

            for slot in slots:
                studio = slot.get("studio", {})
                if studio.get("id") == self._studio_id:
                    course_belongs_to_studio = True
                    break

            if not course_belongs_to_studio:
                continue

            course_name = course.get("name", "Unknown Course")

            for slot in slots:
                # Nur Slots für dieses Studio
                studio = slot.get("studio", {})
                if studio.get("id") != self._studio_id:
                    continue

                start_str = slot.get("startDateTime")
                end_str = slot.get("endDateTime")
                if not start_str or not end_str:
                    continue

                # Remove timezone suffix like '[Europe/Berlin]'
                start_clean = start_str.split("[")[0]
                end_clean = end_str.split("[")[0]

                try:
                    start = datetime.fromisoformat(start_clean)
                    end = datetime.fromisoformat(end_clean)
                except Exception as e:
                    _LOGGER.warning(
                        "Could not parse datetime: %s / %s: %s", start_str, end_str, e
                    )
                    continue

                # Ensure timezone-aware
                if start.tzinfo is None:
                    start = dt_util.as_local(start)
                if end.tzinfo is None:
                    end = dt_util.as_local(end)

                # Convert to UTC
                start_utc = start.astimezone(dt_util.UTC)
                end_utc = end.astimezone(dt_util.UTC)

                if end_utc <= start_date or start_utc >= end_date:
                    continue

                # Build location
                location_parts = []
                if studio_name := studio.get("name"):
                    location_parts.append(studio_name)
                if address := studio.get("address"):
                    if street := address.get("street"):
                        location_parts.append(street)
                    if house := address.get("houseNumber"):
                        location_parts.append(house)
                    if zip_code := address.get("zip"):
                        location_parts.append(zip_code)
                    if city := address.get("city"):
                        location_parts.append(city)
                location = " ".join(location_parts) if location_parts else None

                bookable = course.get("bookable", False)
                description = f"Bookable: {'Yes' if bookable else 'No'}"

                event = CalendarEvent(
                    summary=course_name,
                    start=start_utc,
                    end=end_utc,
                    location=location,
                    description=description,
                )
                events.append(event)

        events.sort(key=lambda e: e.start)
        return events
