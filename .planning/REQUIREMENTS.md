# Requirements: Ducky Thermal Printer

**Defined:** 2026-03-19
**Core Value:** User presses a physical button and a random file prints on the thermal printer

## v0.2 Requirements

Requirements for GPIO Print Trigger milestone. Each maps to roadmap phases.

### Configuration

- [ ] **CFG-01**: User can specify GPIO pin number in YAML config file
- [ ] **CFG-02**: User can set trigger mode (press or switch) in config file
- [ ] **CFG-03**: User can set cooldown duration between activations in config file
- [ ] **CFG-04**: User can set source folder path for print files in config file
- [ ] **CFG-05**: User can set switch trigger direction (both/on_only/off_only) in config file
- [ ] **CFG-06**: System validates config at startup and shows clear error messages for invalid values
- [ ] **CFG-07**: System re-reads config file when it changes without restarting the service

### GPIO Trigger

- [ ] **GPIO-01**: Pressing a button triggers printing a random file from the source folder
- [ ] **GPIO-02**: Flipping a switch triggers printing based on configured transition direction
- [ ] **GPIO-03**: Rapid button presses within cooldown period result in only one print
- [ ] **GPIO-04**: Hardware debounce prevents false triggers from electrical noise
- [ ] **GPIO-05**: Printer failure logs error but does not crash the listener service

### File Selection

- [ ] **FILE-01**: System picks a random file from the configured source folder on each activation
- [ ] **FILE-02**: System filters to supported file types (.txt, .png, .jpg, .bmp)
- [ ] **FILE-03**: Empty source folder logs warning instead of crashing

### Deployment

- [ ] **DEPLOY-01**: GPIO listener runs as a systemd service that starts on boot
- [ ] **DEPLOY-02**: Service restarts automatically on crash
- [ ] **DEPLOY-03**: Service logs to journald for debugging
- [ ] **DEPLOY-04**: usblp kernel module is blacklisted to prevent USB printer conflicts

## Future Requirements

### Web Interface (deferred to v0.3+)

- **WEB-01**: User can trigger print from web browser
- **WEB-02**: Web interface shows print status feedback
- **WEB-03**: Web server runs as systemd service

### WiFi Access Point (deferred to v0.3+)

- **WIFI-01**: Pi creates WiFi access point for direct device connection
- **WIFI-02**: Captive portal redirects to print interface

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multiple printer support | Single Citizen CT-S310IIEBK only for now |
| File upload/management | Uses existing files in source folder |
| Print queue | Single print per activation, cooldown handles rapid triggers |
| Config GUI | YAML file editing is sufficient for Pi users |
| Remote monitoring | journald logs accessible via SSH |
| Cloud connectivity | Standalone device, no cloud dependencies |
| Mobile app | Web interface (future) adequate for mobile |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CFG-01 | TBD | Pending |
| CFG-02 | TBD | Pending |
| CFG-03 | TBD | Pending |
| CFG-04 | TBD | Pending |
| CFG-05 | TBD | Pending |
| CFG-06 | TBD | Pending |
| CFG-07 | TBD | Pending |
| GPIO-01 | TBD | Pending |
| GPIO-02 | TBD | Pending |
| GPIO-03 | TBD | Pending |
| GPIO-04 | TBD | Pending |
| GPIO-05 | TBD | Pending |
| FILE-01 | TBD | Pending |
| FILE-02 | TBD | Pending |
| FILE-03 | TBD | Pending |
| DEPLOY-01 | TBD | Pending |
| DEPLOY-02 | TBD | Pending |
| DEPLOY-03 | TBD | Pending |
| DEPLOY-04 | TBD | Pending |

**Coverage:**
- v0.2 requirements: 19 total
- Mapped to phases: 0
- Unmapped: 19 ⚠️

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after initial definition*
