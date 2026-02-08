# Cardio4HA - Device Health Monitor 🏥

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/nenadjokic/Cardio4HA.svg)](https://github.com/nenadjokic/Cardio4HA/releases)
[![License](https://img.shields.io/github/license/nenadjokic/Cardio4HA.svg)](LICENSE)

> **Your smart home's cardiologist** - Monitor the health of all your devices in one place!

Cardio4HA is a Home Assistant custom integration that acts like a doctor for your smart home. It continuously monitors all your devices and alerts you to problems **before** they become serious issues.

## 🌟 Why Cardio4HA?

If you have **dozens or hundreds** of smart devices, you know the pain:
- 😞 Devices go offline and you don't notice for days
- 🔋 Batteries die without warning
- 📡 Weak signals cause random failures
- 😵 No easy way to see what needs attention

**Cardio4HA solves all of this!**

## ✨ What It Does

✅ **Tracks Unavailable Devices** - Shows which devices are offline and for how long
✅ **Monitors Battery Levels** - Lists all low batteries sorted from worst to best
✅ **Detects Weak Signals** - Finds Zigbee & WiFi devices with poor connectivity
✅ **Device-Level Tracking** - Shows devices, not individual sensors (no clutter!)
✅ **Remembers History** - Tracks how long devices have been unavailable (survives HA restarts!)
✅ **Works Automatically** - No manual configuration needed, just install and go!
✅ **Fast Performance** - Scans 200+ devices in seconds

## 🙏 Support the Project

If you find Cardio4HA helpful, consider supporting its development:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/nenadjokic)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/nenadjokicRS)

⭐ **Star this repo** on GitHub if you find it useful!

---

## 📦 Installation

### Method 1: HACS (Recommended - EASIEST!)

Since this is a custom repository, follow these steps:

1. **Open HACS** in your Home Assistant
2. Click on **"Integrations"** tab
3. Click the **⋮** (three dots menu) in the **top right corner**
4. Select **"Custom repositories"**
5. **Add this repository**:
   - **Repository**: `https://github.com/nenadjokic/Cardio4HA`
   - **Category**: Select **"Integration"**
   - Click **"Add"**
6. **Close the custom repositories dialog**
7. Click **"+ Explore & Download Repositories"** button (bottom right)
8. **Search** for **"Cardio4HA"** or **"Device Health"**
9. Click on **"Cardio4HA"** and then **"Download"**
10. **Restart Home Assistant**
11. Done! Now add the integration ⬇️

### Method 2: Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/nenadjokic/Cardio4HA/releases)
2. Extract the `cardio4ha` folder
3. Copy it to your `config/custom_components/` folder
4. Restart Home Assistant
5. Done! Now add the integration ⬇️

## ⚙️ Setup (Super Easy!)

After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"** in bottom right
3. Search for **"Cardio4HA"** or **"Device Health Monitor"**
4. Click on it
5. Click **"Submit"**
6. **That's it!** ✅

The integration will start monitoring **all your devices automatically** with sensible defaults. No complicated configuration needed!

## 📊 What You Get

After setup, you'll see **7 new sensors**:

| Sensor | What It Shows |
|--------|---------------|
| `sensor.cardio4ha_unavailable_devices` | Number of offline/unavailable devices |
| `sensor.cardio4ha_low_battery_devices` | Number of devices with low battery |
| `sensor.cardio4ha_weak_signal_devices` | Number of devices with weak WiFi/Zigbee signal |
| `sensor.cardio4ha_critical_issues` | Total critical problems needing **immediate** attention |
| `sensor.cardio4ha_warning_issues` | Total warnings that should be checked soon |
| `sensor.cardio4ha_healthy_devices` | Number of healthy devices (everything is OK!) |
| `sensor.cardio4ha_last_scan_duration` | How long the last scan took (in seconds) |

### Viewing Device Details

Each sensor includes a list of affected devices in its **attributes**.

To see details:
1. Go to **Developer Tools** → **States**
2. Find a Cardio4HA sensor
3. Click on it
4. Look at the **"Attributes"** section
5. You'll see a `devices` list with all problematic devices!

Example attribute data:
```yaml
devices:
  - entity_id: sensor.living_room_motion
    name: Living Room Motion Sensor
    duration_human: "3h 25m"
    severity: warning
    area: Living Room
```

## 🎨 Add to Your Dashboard

### Simple Card (Shows counts):

```yaml
type: entities
title: 🏥 Device Health
entities:
  - sensor.cardio4ha_critical_issues
  - sensor.cardio4ha_warning_issues
  - sensor.cardio4ha_unavailable_devices
  - sensor.cardio4ha_low_battery_devices
  - sensor.cardio4ha_weak_signal_devices
  - sensor.cardio4ha_healthy_devices
```

### Summary Card (Numbers only):

```yaml
type: entities
title: 🏥 Device Health Summary
entities:
  - entity: sensor.cardio4ha_critical_issues
    name: Critical Issues
    icon: mdi:alert
  - entity: sensor.cardio4ha_warning_issues
    name: Warning Issues
    icon: mdi:alert-outline
  - entity: sensor.cardio4ha_unavailable_devices
    name: Unavailable Devices
    icon: mdi:alert-circle-outline
  - entity: sensor.cardio4ha_low_battery_devices
    name: Low Battery Devices
    icon: mdi:battery-alert
  - entity: sensor.cardio4ha_weak_signal_devices
    name: Weak Signal Devices
    icon: mdi:signal-off
  - entity: sensor.cardio4ha_healthy_devices
    name: Healthy Devices
    icon: mdi:check-circle
```

### 📋 Detailed List Cards

These cards show device lists with details (name, duration, area, entity ID):

#### ⚠️ Warning Issues Card

```yaml
type: markdown
content: |
  ## ⚠️ WARNING ISSUES {{ states('sensor.cardio4ha_warning_issues') }}

  {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}
  {% if devices %}
  {% for device in devices[:10] %}
  {% if device.severity == 'warning' %}
  - **{{ device.name }}** - Unavailable for {{ device.duration_human }}
    - Entity: `{{ device.entity_id }}`
    - Area: {{ device.area or 'Unknown' }}
  {% endif %}
  {% endfor %}
  {% else %}
  ✅ No warning issues!
  {% endif %}
```

#### 🔴 Unavailable Devices Card

```yaml
type: markdown
content: |
  ## 🔴 UNAVAILABLE DEVICES {{ states('sensor.cardio4ha_unavailable_devices') }}

  {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}
  {% if devices %}
  {% for device in devices[:10] %}
  - **{{ device.name }}**
    - Unavailable for: {{ device.duration_human }}
    - Area: {{ device.area or 'Unknown' }}
    - Entity: `{{ device.entity_id }}`
  {% endfor %}
  {% if state_attr('sensor.cardio4ha_unavailable_devices', 'count') | int > 10 %}

  *... and {{ state_attr('sensor.cardio4ha_unavailable_devices', 'count') | int - 10 }} more*
  {% endif %}
  {% else %}
  ✅ All devices are available!
  {% endif %}
```

#### 🔋 Low Battery Devices Card

```yaml
type: markdown
content: |
  ## 🔋 LOW BATTERY DEVICES {{ states('sensor.cardio4ha_low_battery_devices') }}

  {% set devices = state_attr('sensor.cardio4ha_low_battery_devices', 'devices') %}
  {% if devices %}
  {% for device in devices[:10] %}
  - **{{ device.name }}** - {{ device.battery_level }}%
    - Area: {{ device.area or 'Unknown' }}
    - Entity: `{{ device.entity_id }}`
  {% endfor %}
  {% if state_attr('sensor.cardio4ha_low_battery_devices', 'count') | int > 10 %}

  *... and {{ state_attr('sensor.cardio4ha_low_battery_devices', 'count') | int - 10 }} more*
  {% endif %}
  {% else %}
  ✅ All batteries are good!
  {% endif %}
```

#### 📡 Weak Signal Devices Card

```yaml
type: markdown
content: |
  ## 📡 WEAK SIGNAL DEVICES {{ states('sensor.cardio4ha_weak_signal_devices') }}

  {% set devices = state_attr('sensor.cardio4ha_weak_signal_devices', 'devices') %}
  {% if devices %}
  {% for device in devices[:10] %}
  - **{{ device.name }}**
    {% if device.signal_type == 'zigbee' %}
    - Zigbee LQI: {{ device.linkquality }}
    {% elif device.signal_type == 'wifi' %}
    - WiFi RSSI: {{ device.rssi }} dBm
    {% endif %}
    - Area: {{ device.area or 'Unknown' }}
    - Entity: `{{ device.entity_id }}`
  {% endfor %}
  {% if state_attr('sensor.cardio4ha_weak_signal_devices', 'count') | int > 10 %}

  *... and {{ state_attr('sensor.cardio4ha_weak_signal_devices', 'count') | int - 10 }} more*
  {% endif %}
  {% else %}
  ✅ All signals are strong!
  {% endif %}
```

#### 🎨 Complete Dashboard Example (2x2 Grid with Device Lists)

Put all 4 cards together in a grid:

```yaml
type: grid
columns: 2
square: false
cards:
  # Card 1: Unavailable Devices
  - type: markdown
    content: |
      ## 🔴 UNAVAILABLE {{ states('sensor.cardio4ha_unavailable_devices') }}
      {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      - **{{ device.name }}**
        _{{ device.duration_human }}_
      {% endfor %}
      {% else %}
      ✅ All available!
      {% endif %}

  # Card 2: Low Battery
  - type: markdown
    content: |
      ## 🔋 LOW BATTERY {{ states('sensor.cardio4ha_low_battery_devices') }}
      {% set devices = state_attr('sensor.cardio4ha_low_battery_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      - **{{ device.name }}** - {{ device.battery_level }}%
      {% endfor %}
      {% else %}
      ✅ All good!
      {% endif %}

  # Card 3: Warning Issues
  - type: markdown
    content: |
      ## ⚠️ WARNING {{ states('sensor.cardio4ha_warning_issues') }}
      {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      {% if device.severity == 'warning' %}
      - **{{ device.name }}**
        _{{ device.duration_human }}_
      {% endif %}
      {% endfor %}
      {% else %}
      ✅ No warnings!
      {% endif %}

  # Card 4: Weak Signal
  - type: markdown
    content: |
      ## 📡 WEAK SIGNAL {{ states('sensor.cardio4ha_weak_signal_devices') }}
      {% set devices = state_attr('sensor.cardio4ha_weak_signal_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      - **{{ device.name }}**
      {% endfor %}
      {% else %}
      ✅ All strong!
      {% endif %}
```

**Note:** These markdown cards use Jinja2 templates (works in HA by default). They show top 5 devices for each category with details!

📋 **Want clickable entities and better formatting?** Check out [dashboard-examples.md](dashboard-examples.md) for improved dashboard cards with clickable entity links!

## 🔧 Configuration (Optional)

Want to customize thresholds or exclude devices? Easy!

1. Go to **Settings** → **Devices & Services**
2. Find **Cardio4HA**
3. Click **"Configure"**
4. Adjust these settings:

### Basic Settings

| Setting | What It Does | Default |
|---------|--------------|---------|
| **Update Interval** | How often to scan (seconds) | 60 |

### Battery Thresholds

| Setting | What It Does | Default |
|---------|--------------|---------|
| **Battery Critical** | Level considered critical (%) | 15 |
| **Battery Warning** | Level considered warning (%) | 30 |
| **Battery Low** | Level considered low (%) | 50 |

### Signal Thresholds

| Setting | What It Does | Default |
|---------|--------------|---------|
| **Link Quality Warning** | Zigbee LQI threshold | 100 |
| **RSSI Warning** | WiFi signal threshold (dBm) | -70 |

### Unavailable Thresholds

| Setting | What It Does | Default |
|---------|--------------|---------|
| **Unavailable Warning** | Duration before warning (seconds) | 3600 (1 hour) |
| **Unavailable Critical** | Duration before critical (seconds) | 21600 (6 hours) |

### Advanced Exclusions

| Setting | What It Does | Example |
|---------|--------------|---------|
| **Exclude Entity Wildcards** | Comma-separated wildcard patterns to exclude | `sensor.temp_*, *_battery` |
| **Exclude Integrations** | Integration platforms to exclude from monitoring | Select from list (e.g., `sun`, `updater`) |
| **Exclude Areas** | Areas to exclude from monitoring | Select from list (e.g., `Garage`, `Basement`) |
| **Monitor Zigbee2MQTT** | Always monitor Z2M entities (even if excluded) | ✅ Enabled (recommended) |

**Tip:** Zigbee2MQTT override is enabled by default because Z2M devices often lose signals in practice!

## 🔔 Create Automations

Get notified when critical issues appear:

```yaml
alias: "Alert on Critical Device Issues"
trigger:
  - platform: state
    entity_id: sensor.cardio4ha_critical_issues
    from: "0"
action:
  - service: notify.mobile_app
    data:
      title: "⚠️ Critical Device Issues!"
      message: >
        You have {{ states('sensor.cardio4ha_critical_issues') }}
        critical device issues that need attention!
```

## 🚀 Performance

Cardio4HA is designed for **large installations**:

- ✅ Handles **200+ devices** easily
- ✅ Scans complete in **< 5 seconds**
- ✅ Minimal CPU/memory usage
- ✅ Smart caching to avoid overload

Check the `sensor.cardio4ha_last_scan_duration` to see how fast your system runs!

## ❓ FAQ

### Q: Will this slow down my Home Assistant?
**A:** No! Cardio4HA is optimized for speed and scans every 60 seconds by default without impacting performance.

### Q: Does it work with all integrations?
**A:** Yes! It monitors **any** entity in Home Assistant regardless of the integration.

### Q: What happens if I restart Home Assistant?
**A:** Your unavailable device history is **saved** and restored automatically. You won't lose tracking data!

### Q: Can I exclude certain devices?
**A:** Yes! Use the advanced exclusion system in Configuration. You can exclude by:
- **Wildcard patterns** (e.g., `sensor.temp_*`)
- **Integrations** (e.g., exclude all `sun` or `weather` entities)
- **Areas** (e.g., exclude all devices in "Garage")
- Plus, Zigbee2MQTT entities are always monitored by default (override option available)

### Q: How do I see which specific devices have issues?
**A:** Look at the sensor **attributes** in Developer Tools → States, or wait for the custom Lovelace card (coming soon!).

## 🐛 Troubleshooting

### Integration doesn't appear after restart
1. Check logs: **Settings** → **System** → **Logs**
2. Look for errors mentioning "cardio4ha"
3. Make sure the folder is in `config/custom_components/cardio4ha/`
4. Verify `manifest.json` exists and is valid

### Sensors show "Unknown"
1. Wait 60 seconds for first scan to complete
2. Check `sensor.cardio4ha_last_scan_duration` - if it shows a number, scanning is working
3. Check logs for errors

### Battery devices not detected
1. Make sure entity has `device_class: battery` or contains "battery" in the name
2. Battery level must be between 0-100

## 🗺️ Roadmap

### ✅ Phase 1 - Core Monitoring (DONE!)
- Unavailable device tracking
- Battery monitoring
- Signal detection
- Persistence across restarts
- Device-level tracking (no clutter!)
- Smart unavailable detection

### ✅ Phase 2 - Enhanced Configuration (DONE!)
- Advanced exclusion rules (wildcards, integrations, areas)
- Zigbee2MQTT override for reliability
- Custom thresholds for batteries, signals, and unavailable durations
- Visual configuration UI with multi-select dropdowns
- Clickable dashboard entity links

### 📱 Phase 3 - Custom UI Card (Planned)
- Beautiful Lovelace card
- Sortable tables
- Click to navigate to device
- Visual indicators

### 🔔 Phase 4 - Smart Notifications (Planned)
- Daily health summary
- Instant critical alerts
- Pattern detection (flaky devices)

## 🤝 Contributing

Found a bug? Have an idea?

- 🐛 [Report Issues](https://github.com/nenadjokic/Cardio4HA/issues)
- 💡 [Request Features](https://github.com/nenadjokic/Cardio4HA/issues)
- 🔧 [Submit Pull Requests](https://github.com/nenadjokic/Cardio4HA/pulls)

## 📄 License

MIT License - Free and open source!

---

**Made with ❤️ for the Home Assistant community**

Questions? Open an [issue](https://github.com/nenadjokic/Cardio4HA/issues)!
