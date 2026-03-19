---
phase: 05-gpio-listener
plan: 01
subsystem: gpio-listener
tags: [gpiozero, button, switch, debounce, cooldown, tdd]
dependency_graph:
  requires: [trigger-handler, config-schema]
  provides: [start_gpio_listener]
  affects: [main-service-loop]
tech_stack:
  added: [gpiozero>=2.0]
  patterns: [LGPIOFactory, bounce_time debouncing, cooldown with time.time()]
key_files:
  created:
    - src/gpio_listener.py
    - tests/test_gpio_listener.py
  modified:
    - requirements.txt
decisions:
  - "Use LGPIOFactory explicitly for Pi 3B+ compatibility (gpiozero issue #1090)"
  - "Module-level last_trigger_time for cooldown (simple and thread-safe for single-threaded GPIO callbacks)"
  - "10ms bounce_time default (standard for mechanical buttons)"
  - "InputDevice for switch mode (manual edge detection allows direction filtering)"
  - "ImportError fallback for lgpio (allows testing on non-Pi systems while real Pi has system lgpio)"
metrics:
  duration_seconds: 346
  tasks_completed: 2
  tests_added: 20
  files_created: 2
  commits: 2
  completed_at: "2026-03-19T22:16:13Z"
---

# Phase 05 Plan 01: GPIO Listener Summary

**One-liner**: GPIO button/switch listener with hardware debouncing and cooldown using gpiozero LGPIOFactory for Pi 3B+ compatibility

## What Was Built

Implemented a GPIO event listener that enables physical button presses or switch toggles to trigger random file printing. This satisfies the core value proposition: "user presses a physical button and a random file prints."

### Core Functionality

**Button Mode (trigger_mode="press")**:
- Momentary button press triggers print via `handle_print_trigger(config)`
- Hardware debounce with 10ms bounce_time prevents electrical noise
- Pull-up resistor enabled (button connects to ground)

**Switch Mode (trigger_mode="switch")**:
- Toggle switch with configurable direction:
  - `"both"`: triggers on rising and falling edges
  - `"on_only"`: triggers only on rising edge (switch flipped on)
  - `"off_only"`: triggers only on falling edge (switch flipped off)
- Uses InputDevice for manual edge detection and direction filtering

**Cooldown Protection**:
- Module-level `_last_trigger_time` tracks time between activations
- Prevents rapid-press spam by enforcing minimum delay between prints
- Debug logging shows ignored events within cooldown window
- Zero cooldown disables protection entirely

**Error Resilience**:
- Try-except wrapper catches all exceptions in GPIO callback
- Logs exceptions with stack trace using `logger.exception()`
- Never crashes listener service (GPIO-05 requirement from Phase 04)
- False return from `handle_print_trigger` handled gracefully

### Hardware Compatibility

- LGPIOFactory explicitly set for Raspberry Pi 3B+ (gpiozero issue #1090)
- ImportError fallback allows testing on non-Pi systems
- Real Pi deployment uses system-installed lgpio backend

## Requirements Satisfied

- **GPIO-01**: Button press triggers print via handle_print_trigger
- **GPIO-02**: Switch toggle with direction configuration (both/on_only/off_only)
- **GPIO-03**: Cooldown prevents rapid-press spam with time tracking
- **GPIO-04**: Hardware debounce via bounce_time parameter (10ms default)
- **GPIO-05**: Error resilience inherited from Phase 04 trigger handler

## Testing

**Test Coverage**: 20 tests covering all GPIO behaviors
- Button mode: press triggers, config passing, hardware debounce (3 tests)
- Switch mode: direction filtering (both/on_only/off_only), debounce (4 tests)
- Cooldown: first press, within window, after expiry, tracking, zero cooldown (5 tests)
- Error handling: False return, exceptions logged (2 tests)
- Lifecycle: start/stop, pin factory, config passing (4 tests)
- Hardware: bounce_time verification (2 tests)

**Results**:
- GPIO listener: 20/20 tests passing
- No regressions: Phase 02, 03, 04 tests all pass (54 tests)
- Total: 74/74 tests passing

## Integration Points

**Upstream Dependencies**:
- `src/trigger_handler.handle_print_trigger(config)` - Phase 04 print orchestration
- `src/config/schema.PrinterConfig` - Phase 02 configuration schema

**Downstream Usage**:
- Phase 06 (systemd service) will call `start_gpio_listener(config)` in main loop
- Caller manages lifecycle (keep reference, call `.close()` on shutdown)

## Deviations from Plan

**Auto-fixed Issues**:

**1. [Rule 3 - Blocking] Added gpiozero to requirements.txt**
- **Found during:** Task 1 (RED phase)
- **Issue:** Import error prevented test collection - `ModuleNotFoundError: No module named 'gpiozero'`
- **Fix:** Added `gpiozero>=2.0` to requirements.txt with comment about system lgpio
- **Files modified:** requirements.txt
- **Commit:** a7cf4bf

**2. [Rule 3 - Blocking] Added ImportError fallback for lgpio**
- **Found during:** Task 1 (RED phase)
- **Issue:** lgpio backend not available in venv, blocking test execution
- **Fix:** Wrapped LGPIOFactory import in try-except with fallback to None
- **Rationale:** Tests mock LGPIOFactory, real Pi has system lgpio - allows testing on non-Pi systems
- **Files modified:** src/gpio_listener.py
- **Commit:** a7cf4bf

**3. [Rule 3 - Blocking] Fixed test mock configuration**
- **Found during:** Task 2 (GREEN phase)
- **Issue:** MagicMock auto-creates attributes, breaking assertions for `None` callbacks
- **Fix:** Pre-set `when_activated` and `when_deactivated` to None in switch tests
- **Files modified:** tests/test_gpio_listener.py
- **Commit:** 72ece94

**4. [Rule 3 - Blocking] Removed invalid source_folder from tests**
- **Found during:** Task 2 (GREEN phase)
- **Issue:** Pydantic validation failed for non-existent test folders
- **Fix:** Used default `Path("print_files")` instead of custom paths in tests
- **Files modified:** tests/test_gpio_listener.py
- **Commit:** 72ece94

All deviations were blocking issues (Rule 3) that prevented test execution or caused false failures. No architectural changes needed.

## Technical Decisions

**Module-level _last_trigger_time**:
- Simple and thread-safe for single-threaded GPIO callbacks
- gpiozero uses background threads but callbacks serialize
- Alternative: instance state in closure (more complex, no benefit)

**InputDevice for switch mode**:
- Allows manual edge detection with direction filtering
- Button class doesn't support falling edge callbacks
- Alternative: Two Button instances (wasteful, complex)

**10ms bounce_time**:
- Standard debounce time for mechanical buttons
- gpiozero handles debounce in hardware/driver layer
- Too low: false triggers from noise; too high: missed legitimate presses

**LGPIOFactory explicit setting**:
- Required for gpiozero 2.0+ on Raspberry Pi OS Bookworm
- Default factory (RPi.GPIO) deprecated and incompatible
- Addresses gpiozero issue #1090

**Cooldown enforcement before handler**:
- Update `_last_trigger_time` before calling `handle_print_trigger`
- Prevents race conditions in rapid-fire scenarios
- If handler fails, cooldown still enforced (intentional)

## Files Created/Modified

**Created**:
- `src/gpio_listener.py` (125 lines): GPIO event handling with button/switch modes
- `tests/test_gpio_listener.py` (462 lines): Comprehensive GPIO behavior tests

**Modified**:
- `requirements.txt`: Added gpiozero>=2.0 with lgpio system package note

## Commit History

| Commit | Type | Description |
|--------|------|-------------|
| a7cf4bf | test | Add failing tests for GPIO listener (RED phase) |
| 72ece94 | feat | Implement GPIO listener with button/switch modes (GREEN phase) |

## Next Steps

**Phase 06 - systemd Service**:
- Create main service loop that calls `start_gpio_listener(config)`
- Handle signals (SIGTERM, SIGINT) for graceful shutdown
- Call `listener.close()` on shutdown to clean up GPIO resources
- Integrate config hot-reload from Phase 02
- systemd unit file with dependencies and restart policy

## Self-Check

Verifying deliverables exist:

**Files**:
- [x] src/gpio_listener.py exists
- [x] tests/test_gpio_listener.py exists
- [x] requirements.txt contains gpiozero>=2.0

**Commits**:
- [x] a7cf4bf exists (test commit)
- [x] 72ece94 exists (feat commit)

**Tests**:
- [x] 20 GPIO listener tests passing
- [x] 54 upstream tests passing (no regressions)

**Self-Check: PASSED**
