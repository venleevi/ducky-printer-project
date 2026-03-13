# Requirements: Thermal Printer - User Triggers

**Defined:** 2026-03-13
**Core Value:** Users can trigger thermal printing via physical button or web interface without manual command execution

## v0.2 Requirements

Requirements for user-triggered printing mechanisms. Each maps to roadmap phases.

### Configuration System

- [ ] **CFG-01**: System reads configuration from YAML file
- [ ] **CFG-02**: Configuration specifies whether GPIO trigger is enabled
- [ ] **CFG-03**: Configuration specifies whether web trigger is enabled
- [ ] **CFG-04**: Configuration specifies target file path (wish1.png)
- [ ] **CFG-05**: Configuration specifies GPIO pin number for button

### GPIO Button Trigger

- [ ] **GPIO-01**: Physical button press triggers print of wish1.png
- [ ] **GPIO-02**: Button uses software debouncing to prevent double-press
- [ ] **GPIO-03**: Button applies cooldown period (2s) after successful print
- [ ] **GPIO-04**: GPIO listener runs as systemd service with auto-start
- [ ] **GPIO-05**: GPIO listener handles printer offline errors gracefully
- [ ] **GPIO-06**: GPIO listener respects enable/disable config setting

### Web Interface Trigger

- [ ] **WEB-01**: Web page displays single "Print" button
- [ ] **WEB-02**: Button click sends POST request to trigger print
- [ ] **WEB-03**: Button shows loading state during print operation
- [ ] **WEB-04**: Web page displays success/failure message after print
- [ ] **WEB-05**: Web interface is mobile-responsive (large touch targets)
- [ ] **WEB-06**: Web server runs as systemd service with auto-start
- [ ] **WEB-07**: Web server uses production WSGI server (Waitress)
- [ ] **WEB-08**: Web server respects enable/disable config setting

### Network Access

- [ ] **NET-01**: Web server listens on all network interfaces (0.0.0.0)
- [ ] **NET-02**: Web interface is accessible from devices on same network as Pi
- [ ] **NET-03**: System provides way to display/discover Pi's IP address

### Shared Print Handler

- [ ] **PRINT-01**: Shared handler accepts print requests from GPIO and web triggers
- [ ] **PRINT-02**: Handler implements thread safety for concurrent access
- [ ] **PRINT-03**: Handler calls existing v0.1 printer.print_file() function
- [ ] **PRINT-04**: Handler returns success/failure status to caller
- [ ] **PRINT-05**: Handler maintains v0.1's per-job connection lifecycle

## Future Requirements (v0.3+)

Deferred to future releases. Tracked but not in current roadmap.

### Multi-File Support

- **FILE-01**: Web interface shows list of available files in folder
- **FILE-02**: User can select which file to print from web UI
- **FILE-03**: GPIO button cycles through multiple files

### Advanced Features

- **ADV-01**: Real-time print preview on web interface
- **ADV-02**: Print queue showing pending/completed jobs
- **ADV-03**: Authentication for web interface access
- **ADV-04**: Configuration web panel for editing settings
- **ADV-05**: Multiple GPIO buttons for different files

## Out of Scope

| Feature | Reason |
|---------|--------|
| WiFi Access Point hosting | Pi connects to existing network as client; no need to host its own AP |
| Authentication for web interface | Trusted network environment; authentication adds complexity for single-user device |
| Real-time printer status polling | Thermal printers are simple devices; status checking adds complexity without clear benefit |
| Cloud connectivity | POC is standalone device; cloud adds infrastructure dependencies |
| Mobile app (native) | Web interface adequate for mobile access; native app adds development overhead |
| Bluetooth connectivity | WiFi AP provides sufficient wireless access; Bluetooth adds protocol complexity |
| Multiple concurrent prints | Thermal printer is serial device; queuing adds unnecessary complexity for single-user scenario |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CFG-01 | Phase 2 | Pending |
| CFG-02 | Phase 2 | Pending |
| CFG-03 | Phase 2 | Pending |
| CFG-04 | Phase 2 | Pending |
| CFG-05 | Phase 2 | Pending |
| PRINT-01 | Phase 3 | Pending |
| PRINT-02 | Phase 3 | Pending |
| PRINT-03 | Phase 3 | Pending |
| PRINT-04 | Phase 3 | Pending |
| PRINT-05 | Phase 3 | Pending |
| GPIO-01 | Phase 4 | Pending |
| GPIO-02 | Phase 4 | Pending |
| GPIO-03 | Phase 4 | Pending |
| GPIO-04 | Phase 4 | Pending |
| GPIO-05 | Phase 4 | Pending |
| GPIO-06 | Phase 4 | Pending |
| WEB-01 | Phase 5 | Pending |
| WEB-02 | Phase 5 | Pending |
| WEB-03 | Phase 5 | Pending |
| WEB-04 | Phase 5 | Pending |
| WEB-05 | Phase 5 | Pending |
| WEB-06 | Phase 5 | Pending |
| WEB-07 | Phase 5 | Pending |
| WEB-08 | Phase 5 | Pending |
| NET-01 | Phase 6 | Pending |
| NET-02 | Phase 6 | Pending |
| NET-03 | Phase 6 | Pending |

**Coverage:**
- v0.2 requirements: 27 total
- Mapped to phases: 27 (100%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after roadmap creation*
