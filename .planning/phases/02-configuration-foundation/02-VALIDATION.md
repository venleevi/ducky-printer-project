---
phase: 2
slug: configuration-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
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

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CFG-01 | unit | `pytest tests/test_config_schema.py::test_gpio_pin_validation -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CFG-02 | unit | `pytest tests/test_config_schema.py::test_trigger_mode_validation -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | CFG-03 | unit | `pytest tests/test_config_schema.py::test_cooldown_validation -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | CFG-04 | unit | `pytest tests/test_config_schema.py::test_source_folder_validation -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | CFG-05 | unit | `pytest tests/test_config_schema.py::test_switch_direction_validation -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | CFG-06 | integration | `pytest tests/test_config_loader.py::test_validation_error_messages -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | CFG-07 | integration | `pytest tests/test_config_watcher.py::test_hot_reload -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_config_schema.py` — stubs for CFG-01 through CFG-05
- [ ] `tests/test_config_loader.py` — stubs for CFG-06
- [ ] `tests/test_config_watcher.py` — stubs for CFG-07
- [ ] `tests/conftest.py` — shared fixtures (temp config files, tmp_path)
- [ ] `pip install watchdog` — watchdog not yet in requirements.txt

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GPIO pin hardware access | CFG-01 | Requires physical Raspberry Pi | SSH to Pi, set invalid pin in config, verify error message |
| Config reload on live service | CFG-07 | Requires running service process | Start service, edit config.yaml, verify new values applied within 2s |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
