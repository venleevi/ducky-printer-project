---
phase: 2
slug: configuration-foundation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0+ |
| **Config file** | pytest.ini (exists) |
| **Quick run command** | `pytest tests/test_config.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_config.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 3 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CFG-01..05 | unit | `grep "pyyaml>=6.0.3" requirements.txt` | ✅ | ⬜ pending |
| 02-01-02 | 01 | 1 | CFG-01..05 | unit | `pytest tests/test_config.py -v --collect-only \| grep -c "test_" \| grep -E "^12$"` | ❌ W0 | ⬜ pending |
| 02-02-RED | 02 | 2 | CFG-01..05 | unit | `pytest tests/test_config.py -v` (should fail with ImportError) | ✅ from W1 | ⬜ pending |
| 02-02-GREEN | 02 | 2 | CFG-01..05 | unit | `pytest tests/test_config.py -v` (should pass 12/12) | ✅ from W1 | ⬜ pending |
| 02-02-REFACTOR | 02 | 2 | CFG-01..05 | unit | `pytest tests/test_config.py -v` (should pass 12/12) | ✅ from W1 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_config.py` — 12 test stubs covering CFG-01 through CFG-05 (created by Wave 1 task 02-01-02)
  - test_load_valid_config
  - test_missing_config_file
  - test_invalid_yaml_syntax
  - test_empty_config_file
  - test_gpio_enabled_flag
  - test_web_enabled_flag
  - test_partial_config_uses_defaults
  - test_target_file_path
  - test_path_conversion
  - test_gpio_pin_number
  - test_invalid_gpio_pin_range
  - test_gpio_pin_type_validation
- [x] `tests/conftest.py` — shared fixtures (exists from Phase 1)
- [x] pytest 9.0+ — framework installed (exists in requirements.txt)

**Note:** Wave 1 (plan 02-01) creates test scaffolding. Tests are stubs with `pytest.skip()` markers and verify structure only (12 tests collect successfully). Behavioral verification occurs in Wave 2 (plan 02-02 TDD implementation).

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test scaffold created in Wave 1)
- [x] No watch-mode flags
- [x] Feedback latency < 3s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-13
