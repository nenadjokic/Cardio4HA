"""Constants for Cardio4HA integration."""
from datetime import timedelta

DOMAIN = "cardio4ha"
NAME = "Cardio4HA"
CURRENT_VERSION = "1.1.4"

# GitHub Update Check
GITHUB_RELEASES_URL = "https://api.github.com/repos/nenadjokic/Cardio4HA/releases/latest"
UPDATE_CHECK_INTERVAL = 86400  # 24 hours

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
CONF_EXCLUDE_ENTITY_WILDCARDS = "exclude_entity_wildcards"
CONF_EXCLUDE_INTEGRATIONS = "exclude_integrations"
CONF_EXCLUDE_AREAS = "exclude_areas"
CONF_MONITOR_ZIGBEE2MQTT = "monitor_zigbee2mqtt"

# Configuration - History
CONF_HISTORY_RETENTION_DAYS = "history_retention_days"

# Defaults - Basic
DEFAULT_UPDATE_INTERVAL = 60
DEFAULT_BATTERY_CRITICAL = 15
DEFAULT_BATTERY_WARNING = 30
DEFAULT_BATTERY_LOW = 50
DEFAULT_LINKQUALITY_WARNING = 100
DEFAULT_RSSI_WARNING = -70
DEFAULT_UNAVAILABLE_WARNING = 3600  # 1 hour
DEFAULT_UNAVAILABLE_CRITICAL = 21600  # 6 hours
DEFAULT_EXCLUDE_DOMAINS = [
    # System / HA internals
    "sun", "weather", "updater", "update", "persistent_notification",
    # Automations & scripts
    "automation", "script", "scene", "schedule",
    # Input helpers
    "input_boolean", "input_number", "input_text", "input_select", "input_datetime",
    # Other helpers
    "timer", "counter", "group", "tag",
    # People & zones
    "zone", "person",
    # AI / voice / media
    "conversation", "tts", "stt", "wake_word",
    # Calendar & tasks
    "calendar", "todo", "event",
]
DEFAULT_EXCLUDE_ENTITIES = []
DEFAULT_INCLUDE_DISABLED = False

# Phase 2 Defaults
DEFAULT_EXCLUDE_ENTITY_WILDCARDS = []
DEFAULT_EXCLUDE_INTEGRATIONS = [
    # AI / Conversation
    "openai_conversation",
    "google_generative_ai_conversation",
    "anthropic",
    "ollama",
    # Virtual / Helper sensors
    "template",
    "statistics",
    "derivative",
    "integration",
    "min_max",
    "utility_meter",
    "trend",
    "threshold",
    "bayesian",
    "filter",
    "history_stats",
    "generic_thermostat",
    "generic_hygrostat",
    # System
    "uptime",
    "time_date",
    "version",
    "systemmonitor",
    "local_ip",
    "dnsip",
    "cert_expiry",
    # External data / Cloud
    "rest",
    "command_line",
    "sql",
    "scrape",
    "waze_travel_time",
    "google_translate",
    # Misc virtual
    "random",
    "simulated",
    "demo",
    "proximity",
    "worldclock",
    "github",
    "gitlab_ci",
    "shopping_list",
]
DEFAULT_EXCLUDE_AREAS = []
DEFAULT_MONITOR_ZIGBEE2MQTT = True

# Defaults - History
DEFAULT_HISTORY_RETENTION_DAYS = 30

# Sensor types
SENSOR_UNAVAILABLE_COUNT = "unavailable_count"
SENSOR_LOW_BATTERY_COUNT = "low_battery_count"
SENSOR_WEAK_SIGNAL_COUNT = "weak_signal_count"
SENSOR_CRITICAL_COUNT = "critical_count"
SENSOR_WARNING_COUNT = "warning_count"
SENSOR_HEALTHY_COUNT = "healthy_count"
SENSOR_LAST_SCAN_DURATION = "last_scan_duration"
SENSOR_HEALTH_SCORE = "health_score"
SENSOR_FLAKY_DEVICES_COUNT = "flaky_devices_count"

# Health Score Weights
HEALTH_WEIGHT_UNAVAILABLE = 0.40
HEALTH_WEIGHT_BATTERY = 0.25
HEALTH_WEIGHT_SIGNAL = 0.20
HEALTH_WEIGHT_FLAKY = 0.15

# Storage
STORAGE_KEY = f"{DOMAIN}.unavailable_tracking"
STORAGE_VERSION = 1

# Device History Storage
DEVICE_HISTORY_STORAGE_KEY = f"{DOMAIN}.device_history"
DEVICE_HISTORY_STORAGE_VERSION = 1

# Battery Prediction
BATTERY_READING_INTERVAL = 3600  # 1hr dedup
MIN_BATTERY_READINGS_FOR_PREDICTION = 5

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

# Startup delay (seconds) - wait for HA to fully start before first scan
STARTUP_DELAY = 120

# States to track as unavailable
UNAVAILABLE_STATES = ["unavailable", "unknown"]

# Battery detection keywords
BATTERY_KEYWORDS = ["battery", "batt"]

# Flaky detection
FLAKY_MIN_EVENTS = 3
FLAKY_STDDEV_MULTIPLIER = 1.5

# Service names
SERVICE_MARK_AS_MAINTENANCE = "mark_as_maintenance"
SERVICE_CLEAR_HISTORY = "clear_history"
SERVICE_FORCE_SCAN = "force_scan"
SERVICE_CLEAR_DEVICE_HISTORY = "clear_device_history"
SERVICE_SET_IGNORE = "set_ignore"
SERVICE_CLEAR_IGNORE = "clear_ignore"

# Event types
EVENT_CRITICAL_ISSUE = "cardio4ha_critical_issue"
EVENT_DEVICE_RECOVERED = "cardio4ha_device_recovered"

# Maintenance storage
MAINTENANCE_STORAGE_KEY = f"{DOMAIN}.maintenance_devices"
MAINTENANCE_STORAGE_VERSION = 1

# Ignore storage
IGNORE_STORAGE_KEY = f"{DOMAIN}.ignored_devices"
IGNORE_STORAGE_VERSION = 1

