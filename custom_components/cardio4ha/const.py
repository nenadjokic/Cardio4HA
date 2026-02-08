"""Constants for Cardio4HA integration."""
from datetime import timedelta

DOMAIN = "cardio4ha"
NAME = "Cardio4HA"

# Configuration - Basic
CONF_UPDATE_INTERVAL = "update_interval"
CONF_BATTERY_CRITICAL = "battery_critical"
CONF_BATTERY_WARNING = "battery_warning"
CONF_BATTERY_LOW = "battery_low"
CONF_LINKQUALITY_WARNING = "linkquality_warning"
CONF_RSSI_WARNING = "rssi_warning"
CONF_UNAVAILABLE_WARNING = "unavailable_warning"
CONF_UNAVAILABLE_CRITICAL = "unavailable_critical"
CONF_EXCLUDE_DOMAINS = "exclude_domains"
CONF_EXCLUDE_ENTITIES = "exclude_entities"
CONF_INCLUDE_DISABLED = "include_disabled"

# Configuration - Phase 2: Advanced Exclusions
CONF_EXCLUDE_ENTITY_WILDCARDS = "exclude_entity_wildcards"  # List of wildcard patterns
CONF_EXCLUDE_INTEGRATIONS = "exclude_integrations"  # List of integration platforms to exclude
CONF_EXCLUDE_AREAS = "exclude_areas"  # List of area names to exclude
CONF_MONITOR_ZIGBEE2MQTT = "monitor_zigbee2mqtt"  # Override to always monitor Zigbee2MQTT despite exclusions

# Defaults
DEFAULT_UPDATE_INTERVAL = 60
DEFAULT_BATTERY_CRITICAL = 15
DEFAULT_BATTERY_WARNING = 30
DEFAULT_BATTERY_LOW = 50
DEFAULT_LINKQUALITY_WARNING = 100
DEFAULT_RSSI_WARNING = -70
DEFAULT_UNAVAILABLE_WARNING = 3600  # 1 hour
DEFAULT_UNAVAILABLE_CRITICAL = 21600  # 6 hours
DEFAULT_EXCLUDE_DOMAINS = ["sun", "weather", "updater"]
DEFAULT_EXCLUDE_ENTITIES = []
DEFAULT_INCLUDE_DISABLED = False

# Phase 2 Defaults
DEFAULT_EXCLUDE_ENTITY_WILDCARDS = []
DEFAULT_EXCLUDE_INTEGRATIONS = []
DEFAULT_EXCLUDE_AREAS = []
DEFAULT_MONITOR_ZIGBEE2MQTT = True  # Always monitor Zigbee2MQTT by default

# Sensor types
SENSOR_UNAVAILABLE_COUNT = "unavailable_count"
SENSOR_LOW_BATTERY_COUNT = "low_battery_count"
SENSOR_WEAK_SIGNAL_COUNT = "weak_signal_count"
SENSOR_CRITICAL_COUNT = "critical_count"
SENSOR_WARNING_COUNT = "warning_count"
SENSOR_HEALTHY_COUNT = "healthy_count"
SENSOR_LAST_SCAN_DURATION = "last_scan_duration"

# Storage
STORAGE_KEY = f"{DOMAIN}.unavailable_tracking"
STORAGE_VERSION = 1

# Severity levels
SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_LOW = "low"
SEVERITY_OK = "ok"

# Signal types
SIGNAL_TYPE_ZIGBEE = "zigbee"
SIGNAL_TYPE_WIFI = "wifi"

# Update interval limits
MIN_UPDATE_INTERVAL = 30
MAX_UPDATE_INTERVAL = 300

# States to track as unavailable
UNAVAILABLE_STATES = ["unavailable", "unknown"]

# Battery detection keywords
BATTERY_KEYWORDS = ["battery", "batt"]
