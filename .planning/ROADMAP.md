# Roadmap: Thermal Printer POC

## Milestones

- ✅ **v0.1 POC** — Phase 1 (shipped 2026-03-13)
- 🚧 **v0.2 GPIO Print Trigger** — Phases 2-6 (in progress)

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

### 🚧 v0.2 GPIO Print Trigger

**Milestone Goal:** Physical button or switch connected to Raspberry Pi GPIO triggers printing a random file from a configurable folder, running as a systemd service.

- [x] **Phase 2: Configuration Foundation** - YAML config system with validation, defaults, and hot-reload (COMPLETE 2026-03-19)
- [x] **Phase 3: File Selection** - Random file picker from configurable source folder with type filtering (COMPLETE 2026-03-19)
- [ ] **Phase 4: Trigger Handler** - Integration seam between event sources and print pipeline with error resilience
- [ ] **Phase 5: GPIO Listener** - Button and switch mode GPIO input with debounce and cooldown
- [ ] **Phase 6: Service Deployment** - systemd service, usblp blacklist, journald logging

## Phase Details

### Phase 2: Configuration Foundation
**Goal**: Users can configure all system behavior through a single YAML file with validation and sensible defaults
**Depends on**: Phase 1 (existing v0.1 print pipeline)
**Requirements**: CFG-01, CFG-02, CFG-03, CFG-04, CFG-05, CFG-06, CFG-07
**Success Criteria** (what must be TRUE):
  1. User can edit a YAML config file to set GPIO pin, trigger mode, cooldown, source folder, and switch direction
  2. System starts with sensible defaults when config values are omitted
  3. System refuses to start and prints a clear error message when config contains invalid values (bad pin number, negative cooldown, nonexistent mode)
  4. System picks up config file changes without requiring a service restart
**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Config schema (Pydantic dataclass) and YAML loader with validation and error formatting (COMPLETE)
- [x] 02-02-PLAN.md — Config file hot-reload with watchdog and debouncing (COMPLETE)

### Phase 3: File Selection
**Goal**: System can pick a random printable file from any configured folder
**Depends on**: Phase 2 (reads source folder path from config)
**Requirements**: FILE-01, FILE-02, FILE-03
**Success Criteria** (what must be TRUE):
  1. Each activation selects a random file from the configured source folder
  2. Only supported file types (.txt, .png, .jpg, .jpeg, .bmp) are considered for selection
  3. Empty source folder or folder with no supported files logs a warning instead of crashing
**Plans:** 1 plan

Plans:
- [x] 03-01-PLAN.md — Random file selector with pathlib filtering, case-insensitive extension matching, and graceful empty folder handling (COMPLETE)

### Phase 4: Trigger Handler
**Goal**: A single integration point orchestrates file selection and printing, handling all errors gracefully without crashing the daemon
**Depends on**: Phase 3 (file picker), Phase 1 (print pipeline)
**Requirements**: GPIO-05
**Success Criteria** (what must be TRUE):
  1. A print trigger picks a random file and sends it to the printer through the existing v0.1 pipeline
  2. Printer errors (USB disconnected, paper out, device busy) are logged but do not crash the listener process
  3. File picker errors (empty folder, missing folder) are logged but do not crash the listener process
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: GPIO Listener
**Goal**: Physical button press or switch flip triggers a print with debounce and cooldown protection
**Depends on**: Phase 4 (trigger handler), Phase 2 (config for pin/mode/cooldown)
**Requirements**: GPIO-01, GPIO-02, GPIO-03, GPIO-04
**Success Criteria** (what must be TRUE):
  1. Pressing a GPIO-connected button triggers printing a random file from the source folder
  2. Flipping a GPIO-connected switch triggers printing based on the configured transition direction (both, on_only, or off_only)
  3. Rapid button presses within the cooldown period result in only one print job
  4. Electrical noise from button bounce does not produce false triggers
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

### Phase 6: Service Deployment
**Goal**: The GPIO listener runs unattended on boot with proper logging and USB driver configuration
**Depends on**: Phase 5 (GPIO listener is the service entry point)
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04
**Success Criteria** (what must be TRUE):
  1. After powering on the Raspberry Pi, the GPIO listener service starts automatically without manual intervention
  2. If the service crashes, it restarts automatically within a few seconds
  3. Service output (prints, errors, warnings) is visible in journald logs via `journalctl`
  4. The usblp kernel module is blacklisted so it does not claim the USB printer before the service can access it
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:** 2 -> 3 -> 4 -> 5 -> 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Print files from USB folder | v0.1 | 4/4 | Complete | 2026-03-13 |
| 2. Configuration Foundation | v0.2 | 2/2 | Complete | 2026-03-19 |
| 3. File Selection | v0.2 | 1/1 | Complete | 2026-03-19 |
| 4. Trigger Handler | v0.2 | 0/? | Not started | - |
| 5. GPIO Listener | v0.2 | 0/? | Not started | - |
| 6. Service Deployment | v0.2 | 0/? | Not started | - |

---

*Roadmap created: 2026-03-13*
*Last updated: 2026-03-19 (Phase 3 complete — random file selector with 16 tests, all passing)*
