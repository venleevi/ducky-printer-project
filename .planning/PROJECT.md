# Thermal Printer POC

**Platform:** Raspberry Pi 3B+
**Printer:** Citizen CT-S310IIEBK (USB)
**Language:** Python

## Vision

Proof of concept for automated thermal receipt printing from files stored on a USB stick. The system should detect print jobs in the `/GEN26_BILLPRINTER/` folder and print them on demand using the connected thermal printer.

## Success Criteria

- Successfully communicate with Citizen CT-S310IIEBK via USB
- Read files from USB stick folder `/GEN26_BILLPRINTER/`
- Print file contents to thermal printer
- Handle basic error cases (printer offline, no files, etc.)

## Constraints

- Must run on Raspberry Pi 3B+ (ARM architecture)
- Python-based solution
- USB connectivity only
