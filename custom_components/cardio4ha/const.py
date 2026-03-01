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
CONF_EXCLUDE_ENTITY_WILDCARDS = "exclude_entity_wildcards"
CONF_EXCLUDE_INTEGRATIONS = "exclude_integrations"
CONF_EXCLUDE_AREAS = "exclude_areas"
CONF_MONITOR_ZIGBEE2MQTT = "monitor_zigbee2mqtt"

# Configuration - Notifications
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_INSTANT_ENABLED = "notify_instant_enabled"
CONF_NOTIFY_OFFLINE_MINUTES = "notify_offline_minutes"
CONF_NOTIFY_BATTERY_CRITICAL_LEVEL = "notify_battery_critical_level"
CONF_NOTIFY_MASS_OFFLINE_THRESHOLD = "notify_mass_offline_threshold"
CONF_NOTIFY_DAILY_DIGEST = "notify_daily_digest"
CONF_NOTIFY_DAILY_DIGEST_TIME = "notify_daily_digest_time"
CONF_NOTIFY_RECOVERY_ENABLED = "notify_recovery_enabled"
CONF_NOTIFY_RATE_LIMIT = "notify_rate_limit"
CONF_NOTIFY_DEVICE_COOLDOWN = "notify_device_cooldown"

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
DEFAULT_EXCLUDE_DOMAINS = ["sun", "weather", "updater"]
DEFAULT_EXCLUDE_ENTITIES = []
DEFAULT_INCLUDE_DISABLED = False

# Phase 2 Defaults
DEFAULT_EXCLUDE_ENTITY_WILDCARDS = []
DEFAULT_EXCLUDE_INTEGRATIONS = []
DEFAULT_EXCLUDE_AREAS = []
DEFAULT_MONITOR_ZIGBEE2MQTT = True

# Defaults - Notifications
DEFAULT_NOTIFY_SERVICE = "persistent_notification"
DEFAULT_NOTIFY_INSTANT_ENABLED = True
DEFAULT_NOTIFY_OFFLINE_MINUTES = 15
DEFAULT_NOTIFY_BATTERY_CRITICAL_LEVEL = 10
DEFAULT_NOTIFY_MASS_OFFLINE_THRESHOLD = 3
DEFAULT_NOTIFY_DAILY_DIGEST = True
DEFAULT_NOTIFY_DAILY_DIGEST_TIME = "07:00"
DEFAULT_NOTIFY_RECOVERY_ENABLED = True
DEFAULT_NOTIFY_RATE_LIMIT = 10  # per hour
DEFAULT_NOTIFY_DEVICE_COOLDOWN = 30  # minutes

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

# Notification History Storage
NOTIFICATION_HISTORY_STORAGE_KEY = f"{DOMAIN}.notification_history"
NOTIFICATION_HISTORY_STORAGE_VERSION = 1

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

# Notification types
NOTIFY_TYPE_DEVICE_OFFLINE = "device_offline"
NOTIFY_TYPE_BATTERY_CRITICAL = "battery_critical"
NOTIFY_TYPE_MASS_OFFLINE = "mass_offline"
NOTIFY_TYPE_DEVICE_RECOVERED = "device_recovered"
NOTIFY_TYPE_DAILY_DIGEST = "daily_digest"

# Mass offline window (seconds) - group if N+ devices go offline within this window
MASS_OFFLINE_WINDOW = 300  # 5 minutes
