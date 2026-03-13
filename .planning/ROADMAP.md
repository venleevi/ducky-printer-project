# Roadmap: Thermal Printer POC

## Milestones

- ✅ **v0.1 POC** — Phase 1 (shipped 2026-03-13) — [Details](.planning/milestones/v0.1-ROADMAP.md)
- 🔄 **v0.2 User Triggers** — Phases 2-6 (active) — See phases below

## Phases

<details>
<summary>✅ v0.1 POC (Phase 1) — SHIPPED 2026-03-13</summary>

### Phase 1: Print files from USB folder

**Goal:** Python script that can read files from `/GEN26_BILLPRINTER/` and send them to the Citizen CT-S310IIEBK printer via USB.

**Plans:** 4/4 complete

- [x] 01-01: Foundation setup (requirements, file handler, USB permissions docs)
- [x] 01-02: Core implementation (printer module, test infrastructure)
- [x] 01-03: CLI integration (entry point, full test suite)
- [x] 01-04: Hardware verification (manual testing with real printer)

**Delivered:** Command-line print script for text and images, USB auto-detection, hardware-verified with Citizen CT-S310IIEBK.

</details>

---

### v0.2 User Triggers (Phases 2-6)

- [ ] **Phase 2: Configuration Foundation** - YAML-based config system for trigger control
- [ ] **Phase 3: Shared Print Handler** - Thread-safe print trigger interface
- [ ] **Phase 4: GPIO Button Trigger** - Physical button press printing
- [ ] **Phase 5: Web Interface Core** - HTTP-based print trigger with UI
- [ ] **Phase 6: Network Access** - Network-wide web interface availability

---

## Phase Details

### Phase 2: Configuration Foundation
**Goal**: System loads runtime configuration from YAML file to control trigger behavior

**Depends on**: Nothing (foundation phase)

**Requirements**: CFG-01, CFG-02, CFG-03, CFG-04, CFG-05

**Success Criteria** (what must be TRUE):
1. User can create printer_config.yaml file with GPIO enabled/disabled setting
2. User can specify target print file path (wish1.png) in config file
3. User can specify GPIO pin number in config file
4. User can enable/disable web trigger independently from GPIO trigger
5. System reads config at startup and applies settings without code changes

**Plans**: TBD

---

### Phase 3: Shared Print Handler
**Goal**: Both GPIO and web triggers call unified print function with thread safety

**Depends on**: Phase 2 (needs config system)

**Requirements**: PRINT-01, PRINT-02, PRINT-03, PRINT-04, PRINT-05

**Success Criteria** (what must be TRUE):
1. Trigger handler accepts print request and returns success/failure status
2. Concurrent trigger calls (GPIO + web simultaneously) do not cause USB errors
3. Handler calls existing v0.1 printer.print_file() without modifying it
4. Handler maintains v0.1's per-job connection lifecycle (open-print-close)
5. Failed prints return error status without crashing the calling service

**Plans**: TBD

---

### Phase 4: GPIO Button Trigger
**Goal**: Physical button press triggers print without requiring SSH/keyboard access

**Depends on**: Phase 3 (needs shared handler)

**Requirements**: GPIO-01, GPIO-02, GPIO-03, GPIO-04, GPIO-05, GPIO-06

**Success Criteria** (what must be TRUE):
1. User presses physical button and wish1.png prints on thermal printer
2. Rapid button presses (3 within 1 second) result in only one print job
3. Pressing button within 2 seconds of completed print does nothing (cooldown active)
4. GPIO listener service starts automatically on Pi boot
5. Button press when printer is offline logs error but does not crash service
6. Setting GPIO trigger to disabled in config prevents button from triggering prints

**Plans**: TBD

---

### Phase 5: Web Interface Core
**Goal**: Users can trigger prints from any device with a web browser

**Depends on**: Phase 3 (needs shared handler)

**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04, WEB-05, WEB-06, WEB-07, WEB-08

**Success Criteria** (what must be TRUE):
1. User opens web page and sees single "Print" button
2. User clicks button and sees loading state (button disabled, visual feedback)
3. After print completes, user sees success or failure message on page
4. User can access web interface from mobile phone with large touch targets
5. Web server starts automatically on Pi boot
6. Web server runs on production WSGI server (not Flask dev server)
7. Setting web trigger to disabled in config prevents web server from starting
8. Clicking print button sends POST request that triggers wish1.png print

**Plans**: TBD

---

### Phase 6: Network Access
**Goal**: Web interface is accessible from any device on same network as Raspberry Pi

**Depends on**: Phase 5 (needs web server running)

**Requirements**: NET-01, NET-02, NET-03

**Success Criteria** (what must be TRUE):
1. Web server listens on 0.0.0.0 (all network interfaces, not just localhost)
2. User on same WiFi network as Pi can access web interface via Pi's IP address
3. User can discover Pi's IP address without SSH access (display method provided)

**Plans**: TBD

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Print files from USB folder | v0.1 | 4/4 | Complete | 2026-03-13 |
| 2. Configuration Foundation | v0.2 | 0/? | Not started | - |
| 3. Shared Print Handler | v0.2 | 0/? | Not started | - |
| 4. GPIO Button Trigger | v0.2 | 0/? | Not started | - |
| 5. Web Interface Core | v0.2 | 0/? | Not started | - |
| 6. Network Access | v0.2 | 0/? | Not started | - |

---

## Coverage Map

### v0.2 Requirements (27 total)

| Requirement | Phase | Category |
|-------------|-------|----------|
| CFG-01 | Phase 2 | Configuration |
| CFG-02 | Phase 2 | Configuration |
| CFG-03 | Phase 2 | Configuration |
| CFG-04 | Phase 2 | Configuration |
| CFG-05 | Phase 2 | Configuration |
| PRINT-01 | Phase 3 | Print Handler |
| PRINT-02 | Phase 3 | Print Handler |
| PRINT-03 | Phase 3 | Print Handler |
| PRINT-04 | Phase 3 | Print Handler |
| PRINT-05 | Phase 3 | Print Handler |
| GPIO-01 | Phase 4 | GPIO Trigger |
| GPIO-02 | Phase 4 | GPIO Trigger |
| GPIO-03 | Phase 4 | GPIO Trigger |
| GPIO-04 | Phase 4 | GPIO Trigger |
| GPIO-05 | Phase 4 | GPIO Trigger |
| GPIO-06 | Phase 4 | GPIO Trigger |
| WEB-01 | Phase 5 | Web Interface |
| WEB-02 | Phase 5 | Web Interface |
| WEB-03 | Phase 5 | Web Interface |
| WEB-04 | Phase 5 | Web Interface |
| WEB-05 | Phase 5 | Web Interface |
| WEB-06 | Phase 5 | Web Interface |
| WEB-07 | Phase 5 | Web Interface |
| WEB-08 | Phase 5 | Web Interface |
| NET-01 | Phase 6 | Network |
| NET-02 | Phase 6 | Network |
| NET-03 | Phase 6 | Network |

**Coverage**: 27/27 requirements mapped (100%)

---

*Roadmap created: 2026-03-13*
*Last updated: 2026-03-13 (v0.2 phases added)*
