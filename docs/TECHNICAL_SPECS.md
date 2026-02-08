# Technical Specifications - Cardio4HA

## 🏗️ Architecture Overview

Cardio4HA follows Home Assistant's integration architecture patterns using:
- **DataUpdateCoordinator** for efficient data fetching and caching
- **Config Flow** for UI-based configuration
- **Entity Platform** for sensors and binary sensors
- **Services** for triggering actions
- **Frontend** (separate) for custom Lovelace card

## 📂 Project Structure

```
custom_components/cardio4ha/
├── __init__.py                 # Integration initialization
├── manifest.json               # Integration metadata
├── config_flow.py             # Configuration UI flow
├── const.py                   # Constants and defaults
├── coordinator.py             # Data update coordinator (CORE LOGIC)
├── sensor.py                  # Sensor entities
├── binary_sensor.py           # Binary sensor entities
├── services.yaml              # Service definitions
├── strings.json               # UI strings for config flow
└── translations/
    ├── en.json               # English translations
    └── sr.json               # Serbian translations (optional)

www/cardio4ha-card/            # Custom Lovelace card (separate HACS frontend)
├── cardio4ha-card.js
├── package.json
└── README.md
```

## 🔧 Core Components

### 1. Coordinator (coordinator.py)

**Purpose**: Central data management and update logic

**Key Responsibilities**:
- Scan all entities in Home Assistant
- Track unavailable states with timestamp persistence
- Calculate durations for unavailable entities
- Monitor battery levels across all battery sensors
- Track signal strength (Zigbee LQI, WiFi RSSI)
- Sort and prioritize issues
- Cache results efficiently
- Handle errors gracefully

**Update Interval**: Default 60 seconds (configurable 30-300s)

**Data Structure**:
```python
{
    'unavailable': [
        {
            'entity_id': 'sensor.living_room_motion',
            'name': 'Living Room Motion Sensor',
            'domain': 'sensor',
            'area': 'Living Room',
            'since': datetime,
            'duration_seconds': 12345,
            'duration_human': '3h 25m',
            'last_seen': datetime,
            'integration': 'zha'
        },
        # ... more entries, sorted by duration_seconds DESC
    ],
    'low_battery': [
        {
            'entity_id': 'sensor.bedroom_door_battery',
            'name': 'Bedroom Door Sensor',
            'battery_level': 12,
            'severity': 'critical',  # critical, warning, low
            'area': 'Bedroom',
            'last_updated': datetime
        },
        # ... more entries, sorted by battery_level ASC
    ],
    'weak_signal': [
        {
            'entity_id': 'sensor.garage_motion',
            'name': 'Garage Motion Sensor',
            'signal_type': 'zigbee',  # zigbee or wifi
            'linkquality': 45,  # for Zigbee
            'rssi': None,  # for WiFi
            'area': 'Garage',
            'severity': 'warning'
        },
        # ... more entries, sorted by signal strength ASC
    ],
    'summary': {
        'total_entities': 215,
        'unavailable_count': 5,
        'low_battery_count': 12,
        'weak_signal_count': 8,
        'healthy_count': 190,
        'critical_count': 3,
        'warning_count': 22
    },
    'last_update': datetime,
    'scan_duration': 1.234  # seconds
}
```

### 2. Config Flow (config_flow.py)

**Purpose**: User-friendly configuration interface

**Configuration Options**:

```yaml
Basic Settings:
  name: "Device Health Monitor"  # Integration name
  update_interval: 60  # seconds (30-300)
  
Thresholds:
  battery_critical: 15  # percent
  battery_warning: 30
  battery_low: 50
  
  linkquality_warning: 100  # Zigbee LQI
  rssi_warning: -70  # WiFi RSSI in dBm
  
  unavailable_warning: 3600  # 1 hour in seconds
  unavailable_critical: 21600  # 6 hours in seconds
  
Filters:
  exclude_domains:
    - sun
    - weather
    - automation
    - script
  
  exclude_entities:
    - sensor.sun_*
    - weather.*
  
  include_disabled: false  # Track disabled entities
  
Notifications:
  enabled: true
  instant_critical: true  # Instant notify on critical
  daily_summary: true
  daily_summary_time: "09:00"
  weekly_report: true
  weekly_report_day: "monday"
```

### 3. Sensor Entities (sensor.py)

**Created Sensors**:

```python
# Count sensors
sensor.cardio4ha_unavailable_count       # Number of unavailable devices
sensor.cardio4ha_low_battery_count       # Number of low battery devices
sensor.cardio4ha_weak_signal_count       # Number of weak signal devices
sensor.cardio4ha_critical_count          # Number of critical issues
sensor.cardio4ha_warning_count           # Number of warning issues
sensor.cardio4ha_healthy_count           # Number of healthy devices

# Detail sensors (JSON attributes)
sensor.cardio4ha_unavailable_devices     # Full list as JSON
sensor.cardio4ha_low_battery_devices     # Full list as JSON
sensor.cardio4ha_weak_signal_devices     # Full list as JSON

# Performance sensors
sensor.cardio4ha_last_scan_duration      # How long the scan took
sensor.cardio4ha_last_update             # When was last update
```

**Sensor Attributes**:
Each count sensor includes details in attributes:
```python
{
    'count': 5,
    'devices': [...],  # Top 10 worst
    'severity_breakdown': {
        'critical': 2,
        'warning': 3
    },
    'by_area': {
        'Living Room': 2,
        'Bedroom': 1,
        'Garage': 2
    }
}
```

### 4. Binary Sensors (binary_sensor.py)

```python
binary_sensor.cardio4ha_has_critical_issues      # ON if any critical issues
binary_sensor.cardio4ha_has_warning_issues       # ON if any warnings
binary_sensor.cardio4ha_all_devices_healthy      # ON if all healthy
```

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Home Assistant Core                                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  State Machine (hass.states)                        │  │
│  │  - All entity states                                │  │
│  │  - Attributes                                       │  │
│  │  - Last updated                                     │  │
│  └────────────────┬────────────────────────────────────┘  │
│                   │                                         │
│                   ▼                                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Cardio4HA Coordinator (60s updates)                │  │
│  │  1. Scan all entities                               │  │
│  │  2. Check unavailable states                        │  │
│  │  3. Check battery levels                            │  │
│  │  4. Check signal strengths                          │  │
│  │  5. Calculate durations                             │  │
│  │  6. Sort and prioritize                             │  │
│  │  7. Update cached data                              │  │
│  └────────────────┬────────────────────────────────────┘  │
│                   │                                         │
│         ┌─────────┴─────────┬──────────────┬─────────────┐│
│         ▼                   ▼              ▼             ▼││
│  ┌──────────┐        ┌──────────┐   ┌──────────┐  ┌──────┴┴───┐
│  │ Sensors  │        │  Binary  │   │ Services │  │ Event Bus │
│  │ Entities │        │  Sensors │   │          │  │           │
│  └────┬─────┘        └────┬─────┘   └────┬─────┘  └─────┬─────┘
│       │                   │              │              │    │
└───────┼───────────────────┼──────────────┼──────────────┼────┘
        │                   │              │              │
        ▼                   ▼              ▼              ▼
   Lovelace UI         Automations    Scripts      Notifications
```

## 💾 Data Persistence

### Unavailable Tracking
Must persist across HA restarts to maintain accurate "unavailable since" timestamps.

**Storage Method**: Use Home Assistant's `Store` class

```python
# File: .storage/cardio4ha.unavailable_tracking
{
    'version': 1,
    'data': {
        'sensor.living_room_motion': {
            'since': '2024-02-08T10:30:00Z',
            'entity_id': 'sensor.living_room_motion',
            'name': 'Living Room Motion Sensor'
        },
        # ... more entries
    }
}
```

## 🎯 Performance Requirements

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Scan Duration (200 devices) | < 5s | < 10s |
| Memory Usage | < 50MB | < 100MB |
| CPU Usage (during scan) | < 10% | < 20% |
| Update Interval | 60s | Configurable 30-300s |
| Data Freshness | < 2 minutes old | N/A |

## 🧪 Testing Strategy

### Unit Tests
- Test unavailable detection logic
- Test battery level sorting
- Test signal strength detection
- Test duration calculation
- Test severity classification

### Integration Tests
- Test coordinator updates
- Test sensor entity creation
- Test config flow
- Test data persistence

### Performance Tests
- Test with 200+ entities
- Test update time
- Test memory usage
- Stress test with rapid updates

## 🔐 Security Considerations

- No external API calls (fully local)
- No sensitive data storage
- User configuration stored securely in HA config
- No network exposure required
- Read-only access to HA states

## 📊 Logging Strategy

```python
# Log levels
DEBUG: Detailed scan information, entity processing
INFO: Scan completion, issue counts, configuration changes
WARNING: Performance issues, unusual patterns
ERROR: Failures, exceptions, data corruption
```

## 🚀 Performance Optimization

1. **Batch Processing**: Process entities in batches
2. **Caching**: Cache entity lookups and area mappings
3. **Lazy Loading**: Only load attributes when needed
4. **Incremental Updates**: Track changes, don't rescan everything
5. **Async Operations**: All I/O operations are async

## 🔌 API Design

### Services

```yaml
# Service: cardio4ha.scan_now
# Force immediate scan
cardio4ha.scan_now:

# Service: cardio4ha.clear_history
# Clear unavailable tracking history
cardio4ha.clear_history:
  entity_id: sensor.living_room_motion  # Optional, clear specific or all

# Service: cardio4ha.mark_as_maintenance
# Mark device as in maintenance (ignore temporarily)
cardio4ha.mark_as_maintenance:
  entity_id: sensor.garage_door
  duration: 3600  # seconds (1 hour)
```

### Events

```yaml
# Event: cardio4ha_critical_issue
# Fired when new critical issue detected
event_type: cardio4ha_critical_issue
event_data:
  entity_id: sensor.living_room_motion
  issue_type: unavailable  # or low_battery, weak_signal
  severity: critical
  details: {...}

# Event: cardio4ha_device_recovered  
# Fired when device recovers from issue
event_type: cardio4ha_device_recovered
event_data:
  entity_id: sensor.living_room_motion
  issue_type: unavailable
  duration: 12345  # how long was it unavailable
```

## 📱 Frontend Integration

The custom Lovelace card communicates with the backend through:
- Sensor state subscriptions
- Attribute updates
- Service calls
- WebSocket API

## 🔄 Update Cycle

```
1. Timer triggers (every 60s)
2. Coordinator.async_update_data() called
3. Scan all entities
4. Process unavailable devices
5. Process battery levels
6. Process signal strengths
7. Update persistence storage
8. Calculate summary statistics
9. Update all sensor entities
10. Fire events if needed
11. Return data to coordinator cache
```

## 🎨 Code Style

- Follow Home Assistant development guidelines
- Use type hints throughout
- Async/await for all I/O
- Comprehensive docstrings
- Black formatter
- Pylint/Flake8 compliance

---

**Next**: See PHASE_*.md files for detailed implementation guides
