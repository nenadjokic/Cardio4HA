# 📊 Cardio4HA Dashboard Examples

## 🎨 4-Card Grid (Compact & Clickable)

```yaml
type: grid
columns: 2
square: false
cards:
  # Card 1: Unavailable Devices (CLICKABLE)
  - type: markdown
    content: |
      ## 🔴 UNAVAILABLE {{ states('sensor.cardio4ha_unavailable_devices') }}
      {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      - [**{{ device.name }}**](/config/entities/entity/{{ device.entity_id }}) ({{ device.duration_human }})
      {% endfor %}
      {% if state_attr('sensor.cardio4ha_unavailable_devices', 'count') | int > 5 %}

      *... and {{ state_attr('sensor.cardio4ha_unavailable_devices', 'count') | int - 5 }} more*
      {% endif %}
      {% else %}
      ✅ All available!
      {% endif %}

  # Card 2: Low Battery (CLICKABLE)
  - type: markdown
    content: |
      ## 🔋 LOW BATTERY {{ states('sensor.cardio4ha_low_battery_devices') }}
      {% set devices = state_attr('sensor.cardio4ha_low_battery_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      - [**{{ device.name }}**](/config/entities/entity/{{ device.entity_id }}) {{ device.battery_level }}%
      {% endfor %}
      {% if state_attr('sensor.cardio4ha_low_battery_devices', 'count') | int > 5 %}

      *... and {{ state_attr('sensor.cardio4ha_low_battery_devices', 'count') | int - 5 }} more*
      {% endif %}
      {% else %}
      ✅ All good!
      {% endif %}

  # Card 3: Warning Issues (CLICKABLE)
  - type: markdown
    content: |
      ## ⚠️ WARNING {{ states('sensor.cardio4ha_warning_issues') }}
      {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}
      {% if devices %}
      {% set warning_devices = devices | selectattr('severity', 'eq', 'warning') | list %}
      {% if warning_devices %}
      {% for device in warning_devices[:5] %}
      - [**{{ device.name }}**](/config/entities/entity/{{ device.entity_id }}) ({{ device.duration_human }})
      {% endfor %}
      {% endif %}
      {% endif %}
      {% if not devices or not warning_devices %}
      ✅ No warnings!
      {% endif %}

  # Card 4: Weak Signal (CLICKABLE)
  - type: markdown
    content: |
      ## 📡 WEAK SIGNAL {{ states('sensor.cardio4ha_weak_signal_devices') }}
      {% set devices = state_attr('sensor.cardio4ha_weak_signal_devices', 'devices') %}
      {% if devices %}
      {% for device in devices[:5] %}
      - [**{{ device.name }}**](/config/entities/entity/{{ device.entity_id }})
      {% endfor %}
      {% if state_attr('sensor.cardio4ha_weak_signal_devices', 'count') | int > 5 %}

      *... and {{ state_attr('sensor.cardio4ha_weak_signal_devices', 'count') | int - 5 }} more*
      {% endif %}
      {% else %}
      ✅ All strong!
      {% endif %}
```

## 📋 Critical Issues Card (FIXED)

```yaml
type: vertical-stack
cards:
  - type: conditional
    conditions:
      - entity: sensor.cardio4ha_critical_issues
        state_not: "0"
    card:
      type: markdown
      content: >
        ## ⚠️ CRITICAL ISSUES!

        You have **{{ states('sensor.cardio4ha_critical_issues') }}** devices
        needing immediate attention!
  - type: entities
    title: Device Health Summary
    entities:
      - entity: sensor.cardio4ha_warning_issues
      - entity: sensor.cardio4ha_unavailable_devices
      - entity: sensor.cardio4ha_low_battery_devices
      - entity: sensor.cardio4ha_weak_signal_devices
      - entity: sensor.cardio4ha_healthy_devices
```

## 🔴 Detailed Unavailable Card (Compact & Clickable)

```yaml
type: markdown
content: >
  ## 🔴 UNAVAILABLE {{ states('sensor.cardio4ha_unavailable_devices') }}


  {% set devices = state_attr('sensor.cardio4ha_unavailable_devices', 'devices') %}

  {% if devices %}

  {% for device in devices[:10] %}

  - [**{{ device.name }}**](/config/entities/entity/{{ device.entity_id }}) - {{ device.duration_human }} ({{ device.area or 'Unknown' }})

  {% endfor %}

  {% if state_attr('sensor.cardio4ha_unavailable_devices', 'count') | int > 10 %}


  *... and {{ state_attr('sensor.cardio4ha_unavailable_devices', 'count') | int - 10 }} more*

  {% endif %}

  {% else %}

  ✅ All devices are available!

  {% endif %}
```

## 🎯 Key Features:

1. ✅ **All entity IDs are `sensor.cardio4ha_*`** (correct prefix!)
2. ✅ **Clickable entities** - `[**Name**](/config/entities/entity/entity_id)` opens entity popup
3. ✅ **Compact format** - One line per device
4. ✅ **Shows "... and X more"** when there are more than displayed
5. ✅ **Fixed warning issues filter** - Uses `selectattr` to properly filter by severity

## 📝 Usage:

Copy any of these cards directly into your Lovelace dashboard!
