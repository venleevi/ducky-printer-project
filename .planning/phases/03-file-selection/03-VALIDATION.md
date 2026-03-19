---
phase: 03
slug: file-selection
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-19
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0+ |
| **Config file** | pytest.ini |
| **Quick run command** | `pytest tests/test_file_selector.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_file_selector.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | FILE-01, FILE-02, FILE-03 | unit | `pytest tests/test_file_selector.py -x` | tests/test_file_selector.py | ⬜ pending |
| 03-01-02 | 01 | 1 | FILE-01, FILE-02, FILE-03 | unit | `pytest tests/test_file_selector.py -x` | src/file_selector.py | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Task 03-01-01 creates `tests/test_file_selector.py` with 14 failing tests
- [x] Tests cover FILE-01 (random selection), FILE-02 (extension filtering), FILE-03 (empty folder handling)
- [x] Uses pytest's built-in `tmp_path` and `caplog` fixtures (no new conftest.py additions needed)

*Existing infrastructure covers framework and base fixtures (pytest.ini, conftest.py already configured)*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify elements
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 task creates test file before implementation
- [x] No watch-mode flags
- [x] Feedback latency < 2s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (Wave 0 task structure established)
