"""MySports coordinator using DataUpdateCoordinator."""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .mysports_api import MySportsAPI, MySportsAuthError
from .const import (
    DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
    DEFAULT_CALENDAR_SCAN_INTERVAL,
    CONF_CALENDAR_SCAN_INTERVAL,
    CALENDAR_DAYS_PAST,
    CALENDAR_DAYS_FUTURE,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class MySportsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for studio utilization data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self.api = MySportsAPI(entry.data["username"], entry.data["password"])
        self.studios: list[dict] = []

        interval_minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name="MySports",
            update_interval=timedelta(minutes=interval_minutes),
            always_update=False,
        )

    async def _async_setup(self) -> None:
        """Load studios once before first refresh."""
        await self.hass.async_add_executor_job(self._load_studios)
        if self.studios:
            data = dict(self.config_entry.data)
            data["studios"] = self.studios
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)

    def _load_studios(self) -> None:
        if not self.studios:
            self.studios = self.api.get_studios()
            _LOGGER.debug("Loaded %d studios", len(self.studios))

    def update_interval_from_options(self) -> None:
        """Update the update_interval based on current options."""
        new_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        new_delta = timedelta(minutes=new_interval)
        if self.update_interval != new_delta:
            self.update_interval = new_delta
            self._schedule_refresh()
            _LOGGER.debug("Update interval changed to %d minutes", new_interval)

    def _update_studio_data(self):
        if not self.studios:
            return {
                "studios": {},
                "last_update": None,
                "authenticated": self.api.is_authenticated,
                "error": "No studios found",
            }

        result = {
            "studios": {},
            "last_update": None,
            "authenticated": self.api.is_authenticated,
        }

        for studio in self.studios:
            studio_id = studio["id"]
            studio_name = studio["name"]
            logo_url = studio.get("logo_url")
            try:
                active_count = self.api.get_utilization(studio_id)
                result["studios"][studio_id] = {
                    "id": studio_id,
                    "name": studio_name,
                    "primary": studio.get("primary", False),
                    "logo_url": logo_url,
                    "active_checkins": (
                        active_count if active_count is not None else None
                    ),
                    "available": active_count is not None,
                }
            except MySportsAuthError as e:
                _LOGGER.error("Permanent authentication error: %s", e)
                raise
            except Exception as e:
                _LOGGER.error("Error fetching utilization for %s: %s", studio_name, e)
                result["studios"][studio_id] = {
                    "id": studio_id,
                    "name": studio_name,
                    "primary": studio.get("primary", False),
                    "logo_url": logo_url,
                    "active_checkins": None,
                    "available": False,
                    "error": str(e),
                }

        if any(s.get("available", False) for s in result["studios"].values()):
            result["last_update"] = datetime.now().isoformat()
        return result

    async def _async_update_data(self):
        try:
            data = await self.hass.async_add_executor_job(self._update_studio_data)
            return data
        except MySportsAuthError as err:
            _LOGGER.warning("Authentication failed, starting reauthentication: %s", err)
            self.config_entry.async_start_reauth(self.hass)
            raise ConfigEntryAuthFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def get_studio_data(self, studio_id: int) -> dict:
        return self.data.get("studios", {}).get(studio_id, {})

    def get_studio_logo_url(self, studio_id: int) -> str | None:
        studio_data = self.get_studio_data(studio_id)
        return studio_data.get("logo_url") if studio_data else None

    def get_all_studios(self) -> list:
        return self.studios

    async def async_reauthenticate(self):
        await self.hass.async_add_executor_job(self.api.logout)
        await self._async_update_data()


class MySportsCoursesCoordinator(DataUpdateCoordinator[List[dict]]):
    """Coordinator for course data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: MySportsAPI,
        studios: list[dict],
    ) -> None:
        self.config_entry = entry
        self.api = api
        self.studios = studios

        interval_minutes = entry.options.get(
            CONF_CALENDAR_SCAN_INTERVAL, DEFAULT_CALENDAR_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name="MySports Courses",
            update_interval=timedelta(minutes=interval_minutes),
            always_update=False,
        )

    async def _async_update_data(self) -> List[dict]:
        """Fetch courses for all studios."""
        if not self.studios:
            return []

        # Calculate date range: from CALENDAR_DAYS_PAST days ago to CALENDAR_DAYS_FUTURE days in future
        today = datetime.now()
        start_date = today - timedelta(days=CALENDAR_DAYS_PAST)
        end_date = today + timedelta(days=CALENDAR_DAYS_FUTURE)

        # Collect all organization unit IDs from studios
        org_unit_ids = [studio["id"] for studio in self.studios if studio.get("id")]

        if not org_unit_ids:
            return []

        try:
            courses = await self.hass.async_add_executor_job(
                self.api.get_courses, start_date, end_date, org_unit_ids
            )
            return courses
        except MySportsAuthError as e:
            _LOGGER.warning("Auth error during courses update: %s", e)
            self.config_entry.async_start_reauth(self.hass)
            raise ConfigEntryAuthFailed(str(e)) from e
        except Exception as e:
            _LOGGER.error("Error fetching courses: %s", e)
            raise UpdateFailed(f"Error fetching courses: {e}") from e

    def get_all_courses(self) -> List[dict]:
        """Return the latest course data."""
        return self.data if self.data else []
