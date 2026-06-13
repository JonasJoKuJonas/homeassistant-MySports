"""Constants for MySports integration."""

from homeassistant.const import Platform

DOMAIN = "mysports"
DEFAULT_SCAN_INTERVAL = 30  # minutes (for utilization)
MIN_SCAN_INTERVAL = 10  # minutes
CONF_SCAN_INTERVAL = "scan_interval"

# Calendar related constants
DEFAULT_CALENDAR_SCAN_INTERVAL = 360  # minutes
MIN_CALENDAR_SCAN_INTERVAL = 30
CONF_CALENDAR_SCAN_INTERVAL = "calendar_scan_interval"

CALENDAR_DAYS_PAST = 7  # 1 week past
CALENDAR_DAYS_FUTURE = 28  # 4 weeks future

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]
