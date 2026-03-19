# Thermal Printer POC

**Platform:** Raspberry Pi 3B+
**Printer:** Citizen CT-S310IIEBK (USB)
**Language:** Python

## What This Is

A Raspberry Pi-based thermal printing system that prints files from a USB-connected Citizen CT-S310IIEBK printer. Users trigger prints via physical GPIO button or switch, printing a random file from a configurable folder. Runs as a systemd service on boot.

## Core Value

User presses a physical button (or flips a switch) and a random file prints on the thermal printer — no screen, keyboard, or SSH required.

## Requirements

### Validated

- ✓ USB thermal printer communication with auto-detection — v0.1
- ✓ Text file printing (.txt) with UTF-8 support — v0.1
- ✓ Image file printing (.png, .jpg, .bmp) — v0.1
- ✓ CLI print interface (`python3 -m src.print_job <filename>`) — v0.1
- ✓ Error handling with proper exit codes — v0.1

### Active

- [ ] YAML configuration system (GPIO pin, mode, cooldown, source path)
- [ ] GPIO button press triggers random file print
- [ ] GPIO switch mode with configurable transition triggers (both/on_only/off_only)
- [ ] Configurable cooldown between activations (default 5s)
- [ ] Random file selection from configurable source folder
- [ ] systemd service for auto-start on boot

### Out of Scope

- Web interface — deferred to future milestone
- WiFi access point configuration — deferred to future milestone
- Multiple printer support — single printer only
- File upload or management — uses existing files in source folder

## Context

- v0.1 POC shipped 2026-03-13 with CLI-only printing
- v0.2 was originally scoped with web interface + GPIO + config; descoped to GPIO-only focus
- Existing `src.print_job` module handles file-to-printer pipeline
- Per-job USB connection lifecycle (open-print-close) must be maintained
- RPi.GPIO or gpiozero needed for GPIO access on Pi 3B+

## Constraints

- **Platform**: Raspberry Pi 3B+ (ARM architecture, Debian-based OS)
- **Language**: Python (existing codebase)
- **Integration**: Must use existing v0.1 print pipeline without modifying it
- **Connection**: Per-job USB connection lifecycle must be maintained for thread safety
- **Dependencies**: Minimize new dependencies (PyYAML for config, GPIO library for hardware)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| USB class 7 detection instead of vendor/product IDs | Works across multiple printer models | ✓ Good |
| Per-job connection lifecycle (open-print-close) | Prevents device busy errors after power cycles | ✓ Good |
| Extended to support images (PNG/JPG/BMP) | Real USB folder contained image files needing printing | ✓ Good |
| Explicit USB endpoints (in_ep=0x81, out_ep=0x02) | Required for Citizen CT-S310IIEBK compatibility | ✓ Good |
| YAML config over JSON/INI | Human-friendly for Pi users editing config on device | — Pending |
| GPIO trigger only (no web) for v0.2 | Focused scope, ship faster, web deferred | — Pending |

## Current Milestone: v0.2 GPIO Print Trigger

**Goal:** Physical button or switch connected to Raspberry Pi GPIO triggers printing a random file from a configurable folder, running as a systemd service.

**Target features:**
- YAML configuration system
- GPIO button/switch listener with configurable mode
- Random file selection from source folder
- Cooldown between activations
- systemd service for auto-start on boot

---
*Last updated: 2026-03-19 after starting v0.2 milestone*
