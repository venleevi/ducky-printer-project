---
phase: 2
slug: configuration-foundation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-19
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0+ |
| **Config file** | pytest.ini (exists, configured with pythonpath) |
| **Quick run command** | `pytest tests/test_config_schema.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_config_schema.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Wave 0 / Nyquist Compliance Note

Both plans (02-01 and 02-02) use `type: tdd` with `tdd="true"` tasks. In TDD plans, test files are created during the RED phase of each task — tests are written BEFORE implementation code. This satisfies the Nyquist requirement because:

1. **test_config_schema.py** — Created in Plan 01, Task 1 RED phase (step 3) before any schema implementation
2. **test_config_loader.py** — Created in Plan 01, Task 2 RED phase (step 1) before any loader implementation
3. **test_config_watcher.py** — Created in Plan 02, Task 1 RED phase (step 2) before any watcher implementation
4. **conftest.py** — Created in Plan 01, Task 1 RED phase (step 4) with shared fixtures

No separate Wave 0 plan is needed — the TDD RED phase IS the test scaffold creation step.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Test Created In | Status |
|---------|------|------|-------------|-----------|-------------------|-----------------|--------|
| 02-01-01 | 01 | 1 | CFG-01 | unit | `pytest tests/test_config_schema.py::test_gpio_pin_validation -x` | Task 1 RED phase | pending |
| 02-01-02 | 01 | 1 | CFG-02 | unit | `pytest tests/test_config_schema.py::test_trigger_mode_validation -x` | Task 1 RED phase | pending |
| 02-01-03 | 01 | 1 | CFG-03 | unit | `pytest tests/test_config_schema.py::test_cooldown_validation -x` | Task 1 RED phase | pending |
| 02-01-04 | 01 | 1 | CFG-04 | unit | `pytest tests/test_config_schema.py::test_source_folder_validation -x` | Task 1 RED phase | pending |
| 02-01-05 | 01 | 1 | CFG-05 | unit | `pytest tests/test_config_schema.py::test_switch_direction_validation -x` | Task 1 RED phase | pending |
| 02-02-01 | 01 | 1 | CFG-06 | integration | `pytest tests/test_config_loader.py::test_validation_error_messages -x` | Task 2 RED phase | pending |
| 02-03-01 | 02 | 2 | CFG-07 | integration | `pytest tests/test_config_watcher.py::test_hot_reload -x` | Task 1 RED phase | pending |

*Status: pending / green / red / flaky*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GPIO pin hardware access | CFG-01 | Requires physical Raspberry Pi | SSH to Pi, set invalid pin in config, verify error message |
| Config reload on live service | CFG-07 | Requires running service process | Start service, edit config.yaml, verify new values applied within 2s |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or TDD RED phase creates tests first
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covered by TDD RED phases (test files created before implementation)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (TDD plans satisfy Nyquist via RED phase test creation)
