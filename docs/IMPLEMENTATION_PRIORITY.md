# Implementation Priority & Quick Start Guide

## 🎯 Development Order (Strict Priority)

### PRIORITY 1: Core Functionality (Week 1)
**Goal**: Get basic monitoring working

1. **Day 1-2**: Project Setup
   - ✅ Create file structure
   - ✅ manifest.json
   - ✅ const.py
   - ✅ Basic __init__.py

2. **Day 3-5**: Coordinator Implementation
   - ✅ Unavailable device tracking
   - ✅ Battery monitoring
   - ✅ Signal detection
   - ✅ Storage system
   - ✅ Sorting logic

3. **Day 6-7**: Sensor Entities
   - ✅ Count sensors
   - ✅ Attributes
   - ✅ Testing

**Deliverable**: Working integration that tracks devices

---

### PRIORITY 2: Configuration (Week 2)
**Goal**: Make it user-configurable

1. **Day 1-3**: Config Flow
   - ✅ config_flow.py
   - ✅ User input validation
   - ✅ Options flow
   - ✅ Threshold configuration

2. **Day 4-5**: Binary Sensors
   - ✅ binary_sensor.py
   - ✅ Critical issue detector
   - ✅ Warning detector

3. **Day 6-7**: Testing & Polish
   - ✅ Test all thresholds
   - ✅ Test exclusions
   - ✅ Error handling

**Deliverable**: Fully configurable integration

---

### PRIORITY 3: Lovelace Card (Week 3)
**Goal**: Beautiful UI

1. **Day 1-3**: Basic Card
   - ✅ Card skeleton
   - ✅ Tab interface
   - ✅ Summary statistics

2. **Day 4-5**: Table Views
   - ✅ Unavailable table
   - ✅ Battery table
   - ✅ Signal table

3. **Day 6-7**: Polish
   - ✅ Styling
   - ✅ Icons
   - ✅ Responsive design

**Deliverable**: Custom card installable via HACS

---

### PRIORITY 4: Notifications (Week 4)
**Goal**: Smart alerting

1. **Day 1-2**: Service Implementation
   - ✅ services.yaml
   - ✅ Service handlers

2. **Day 3-4**: Notification Logic
   - ✅ Event firing
   - ✅ Threshold-based alerts
   - ✅ Daily summary

3. **Day 5-7**: Testing
   - ✅ Test notifications
   - ✅ Test daily summary
   - ✅ Integration tests

**Deliverable**: Working notification system

---

## 🚀 Quick Start Commands for Claude Code

### Initial Setup
```bash
# Create project structure
cd /path/to/homeassistant/config/custom_components
mkdir -p cardio4ha
cd cardio4ha

# Create all necessary files
touch __init__.py manifest.json const.py coordinator.py sensor.py binary_sensor.py config_flow.py services.yaml strings.json
```

### Phase 1: Core Implementation
```bash
# Start with Claude Code - give it this prompt:
"Read all MD files in /path/to/cardio4ha_docs and implement Phase 1.
Start with manifest.json and const.py, then implement coordinator.py 
with full unavailable tracking, battery monitoring, and signal detection.
Ensure data persists across HA restarts using Store class.
Create sensor.py with all count sensors.
Follow all specifications in PHASE_1_CORE.md exactly."
```

### Phase 2: Config Flow
```bash
# Claude Code prompt:
"Implement config_flow.py with user-friendly configuration UI.
Include all threshold settings, exclusion options, and validation.
Add binary_sensor.py with critical and warning issue detectors.
Follow TECHNICAL_SPECS.md for exact configuration options."
```

### Phase 3: Lovelace Card
```bash
# Create separate repository for card
mkdir cardio4ha-card
cd cardio4ha-card

# Claude Code prompt:
"Create custom Lovelace card for Cardio4HA with tabs for
Unavailable, Battery, Signal, and All Devices. Use Lit framework.
Include summary statistics and sortable tables. Follow Home Assistant
card development guidelines."
```

### Phase 4: Notifications
```bash
# Claude Code prompt:
"Add notification system to coordinator.py. Implement services
for manual scan, clear history, and mark as maintenance.
Create event firing for critical issues and device recovery.
Add daily summary automation blueprint."
```

---

## 📝 File-by-File Implementation Guide

### 1. manifest.json (5 minutes)
```bash
# Copy from PHASE_1_CORE.md
# Update domain, name, and your details
```

### 2. const.py (10 minutes)
```bash
# Copy all constants from PHASE_1_CORE.md
# Review defaults and adjust if needed
```

### 3. __init__.py (15 minutes)
```bash
# Copy from PHASE_1_CORE.md
# Ensure proper platform loading
# Add reload listener
```

### 4. coordinator.py (2-3 hours) ⚠️ MOST IMPORTANT
```bash
# This is the heart of the integration
# Carefully implement:
# - Storage system
# - Entity scanning
# - Unavailable tracking with timestamp
# - Battery detection and sorting
# - Signal strength monitoring
# - Duration calculations
# - Performance optimization
```

### 5. sensor.py (1 hour)
```bash
# Create all sensor entities
# Add proper attributes
# Ensure coordinator updates trigger sensor updates
```

### 6. binary_sensor.py (30 minutes)
```bash
# Simple ON/OFF sensors for automations
# Critical issues detector
# Warning issues detector
```

### 7. config_flow.py (1-2 hours)
```bash
# User configuration UI
# Validation logic
# Options flow for reconfiguration
```

---

## 🧪 Testing Strategy

### Unit Tests
Create `tests/test_coordinator.py`:
```python
"""Tests for coordinator."""
import pytest
from homeassistant.core import HomeAssistant

async def test_unavailable_detection(hass: HomeAssistant):
    """Test unavailable device detection."""
    # Test logic here
    
async def test_battery_sorting(hass: HomeAssistant):
    """Test battery devices are sorted correctly."""
    # Test logic here
```

### Integration Tests
```bash
# Test with real HA instance
1. Install integration
2. Verify sensors created
3. Make device unavailable
4. Check tracking persists after restart
5. Verify battery detection
6. Test performance with 200+ devices
```

### Performance Benchmarks
```python
# Add to coordinator.py for testing
_LOGGER.info(
    "Scan stats: %d entities, %.2fs scan time, %.2fms per entity",
    total_entities,
    scan_duration,
    (scan_duration / total_entities * 1000) if total_entities > 0 else 0
)
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Slow Scanning
**Problem**: Scan takes >10 seconds
**Solution**: 
- Add batching: Process entities in chunks
- Optimize entity registry lookups
- Cache device/area mappings
- Use async properly

### Issue 2: Persistence Not Working
**Problem**: Unavailable tracking resets on restart
**Solution**:
- Check storage file exists: `.storage/cardio4ha.unavailable_tracking`
- Verify async_load_unavailable_data() is called
- Check datetime serialization

### Issue 3: Battery Sensors Not Detected
**Problem**: No low battery devices shown
**Solution**:
- Check BATTERY_KEYWORDS in const.py
- Verify device_class attribute check
- Add logging to see what's being checked

### Issue 4: Sensors Not Updating
**Problem**: Sensor shows "Unknown"
**Solution**:
- Verify coordinator update_interval
- Check for errors in coordinator logs
- Ensure sensors are listening to coordinator

---

## 📦 Packaging for HACS

### Step 1: Create Repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/cardio4ha.git
git push -u origin main
```

### Step 2: Add HACS Files
Create `hacs.json`:
```json
{
  "name": "Cardio4HA - Device Health Monitor",
  "content_in_root": false,
  "filename": "cardio4ha",
  "homeassistant": "2024.1.0",
  "render_readme": true
}
```

### Step 3: Create README.md
```markdown
# Cardio4HA - Device Health Monitor for Home Assistant

[Add badges, description, installation instructions]
```

### Step 4: Tag Release
```bash
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

---

## 🎯 Success Metrics

### Phase 1 Complete When:
- ✅ Integration installs without errors
- ✅ All sensors created and showing data
- ✅ Unavailable tracking persists across restarts
- ✅ Battery devices detected and sorted correctly
- ✅ Signal issues detected
- ✅ Scan completes in <5 seconds for 200 devices
- ✅ No errors in logs

### Phase 2 Complete When:
- ✅ Config flow works perfectly
- ✅ All thresholds configurable
- ✅ Exclusions work
- ✅ Binary sensors created
- ✅ Options flow allows reconfiguration

### Phase 3 Complete When:
- ✅ Custom card installable via HACS
- ✅ All tabs work
- ✅ Data displays correctly
- ✅ Responsive on mobile
- ✅ Looks professional

### Phase 4 Complete When:
- ✅ Notifications fire correctly
- ✅ Services work
- ✅ Daily summary automation works
- ✅ Events fire on critical issues

---

## 📚 Additional Resources

### Home Assistant Development
- https://developers.home-assistant.io/
- https://developers.home-assistant.io/docs/creating_integration_manifest
- https://developers.home-assistant.io/docs/config_entries_config_flow_handler

### Lovelace Card Development  
- https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card
- https://lit.dev/ (Lit framework)

### HACS
- https://hacs.xyz/docs/publish/integration
- https://hacs.xyz/docs/publish/include

---

## 💡 Pro Tips

1. **Start Simple**: Get basic monitoring working first, then add features
2. **Test Early**: Don't wait until everything is done to test
3. **Use Logging**: Add lots of DEBUG logs during development
4. **Performance First**: Test with 200+ devices early
5. **Read Other Integrations**: Look at similar HA integrations for patterns
6. **Ask Community**: Home Assistant Discord is very helpful

---

## 🎬 Let's Start!

**Recommended Claude Code First Prompt:**

```
I want to create a Home Assistant HACS integration called Cardio4HA 
that monitors device health. I have complete documentation in MD files.

Please:
1. Read all files in /path/to/cardio4ha_docs/
2. Start with PROJECT_OVERVIEW.md to understand the vision
3. Read TECHNICAL_SPECS.md for architecture
4. Implement PHASE_1_CORE.md completely
5. Create all necessary files in custom_components/cardio4ha/
6. Ensure code follows HA best practices
7. Add comprehensive logging
8. Test with 200+ entity scenario

Focus on coordinator.py - this is the most critical file.
Implement unavailable tracking with persistence, battery monitoring,
and signal detection. Sort results correctly.

Let's build an amazing device health monitor!
```

---

Good luck! 🚀
