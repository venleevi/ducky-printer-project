---
phase: 02-configuration-foundation
plan: 02
subsystem: configuration
tags: [watchdog, hot-reload, file-monitoring, debouncing]

# Dependency graph
requires:
  - phase: 02-01
    provides: load_config() and PrinterConfig schema
provides:
  - ConfigWatcher with debounced file change detection
  - start_config_watcher() lifecycle management
  - Error-resilient reload callback handling
  - Support for atomic editor saves (on_modified + on_created events)
affects: [main-application-loop]

# Tech tracking
tech-stack:
  added: [watchdog>=6.0]
  patterns: [FileSystemEventHandler for config monitoring, debouncing with time.time(), exception handling in callbacks to prevent crash]

key-files:
  created:
    - src/config/watcher.py
    - tests/test_config_watcher.py
  modified:
    - src/config/__init__.py
    - requirements.txt

key-decisions:
  - "Handle both on_modified and on_created events to support atomic editor saves (write temp + rename pattern)"
  - "1 second debounce window to prevent reload spam from rapid saves"
  - "Log exceptions in reload callback but keep watcher running (resilience over fail-fast)"
  - "Watch parent directory (not file directly) to catch file recreation/rename events"
  - "Use Python logging module (not print) for service/systemd compatibility"

patterns-established:
  - "Hot-reload pattern: Observer + FileSystemEventHandler + debounce + exception safety"
  - "Lifecycle: start_config_watcher() returns Observer, caller manages stop/join"
  - "Test timing: Polling loop pattern (for _ in range(20): sleep 0.1; check condition) instead of single long sleep"

requirements-completed: [CFG-07]

# Metrics
duration: ~50min
completed: 2026-03-19
---

# Phase 02-02: Config Hot-Reload Watcher Summary

**watchdog-based file monitoring with 1s debouncing, atomic save support (on_modified + on_created), and error-resilient callback handling**

## Performance

- **Duration:** ~50 minutes (implementation + test creation)
- **Started:** 2026-03-19 ~21:10
- **Completed:** 2026-03-19 ~22:00 (tests added in continuation session)
- **Tasks:** 1
- **Files created:** 2
- **Files modified:** 2

## Accomplishments
- ConfigWatcher handles rapid file saves with 1-second debouncing (prevents reload spam)
- Detects both FileModifiedEvent and FileCreatedEvent to support atomic editor saves (vim, nano, VS Code patterns)
- Survives invalid config errors in reload callback - logs exception but keeps watcher running
- Clean start/stop lifecycle with Observer.stop() + join()
- 6 tests validate debouncing, error resilience, file filtering, and lifecycle management

## Task Commits

1. **Task 1: Config watcher with debouncing** - `8731d58` (feat: dev commit with implementation)
   - ConfigWatcher class with _handle_event() debouncing logic
   - start_config_watcher() returns stoppable Observer
   - Exception safety: try/except around reload_callback with logger.exception

2. **Test completion** - `30c5f85` (test: config watcher tests)
   - 6 tests covering file change detection, debouncing, error survival, file filtering, lifecycle

## Files Created/Modified

**Created:**
- `src/config/watcher.py` - ConfigWatcher(FileSystemEventHandler) with debounce logic and start_config_watcher() function
- `tests/test_config_watcher.py` - 6 watcher integration tests (file change, debounce, error resilience, filtering, lifecycle)

**Modified:**
- `src/config/__init__.py` - Added ConfigWatcher and start_config_watcher to exports
- `requirements.txt` - Added watchdog>=6.0 with comment

## Decisions Made

- **Both on_modified and on_created events**: Editors use different save patterns (vim/nano do atomic writes via temp files, triggering on_created instead of on_modified)
- **1 second debounce**: Balances responsiveness (picks up changes quickly) with stability (prevents reload spam from auto-save or rapid edits)
- **Log but don't crash on callback errors**: Service should stay running even if config reload fails (e.g., syntax error in YAML) - logs exception for debugging
- **Watch parent directory**: Watching the file directly misses rename/recreation events; watching parent catches all file operations
- **Polling loop in tests**: `for _ in range(20): sleep(0.1)` instead of `sleep(2)` - keeps tests fast when events arrive quickly, tolerant when slow

## Deviations from Plan

None - plan executed as specified. All 6 behavior tests from plan passed on first run.

## Issues Encountered

**Test timing sensitivity**: File system event propagation is async, so tests use polling loops with 0.1s intervals (max 2s wait) instead of fixed sleeps. This makes tests fast on CI but tolerant on slow systems.

## User Setup Required

None - watchdog installed via `pip install -r requirements.txt` (already done in venv).

## Next Phase Readiness

- Configuration foundation complete (CFG-01 through CFG-07 satisfied)
- Phase 03 (File Picker) can use load_config() to get source_folder
- Main application loop can use start_config_watcher() to reload config on file changes
- All 35 config tests pass (19 schema + 10 loader + 6 watcher)
- Ready to integrate config system into main.py service loop

## Test Summary

**All Phase 02 tests: 35/35 passing**
- test_config_schema.py: 19/19 ✓
- test_config_loader.py: 10/10 ✓
- test_config_watcher.py: 6/6 ✓

**Note:** 6 v0.1 tests have pre-existing failures (path expectations changed after project restructure). Phase 02 work did not introduce regressions.

---
*Phase: 02-configuration-foundation*
*Plan: 02*
*Completed: 2026-03-19*
