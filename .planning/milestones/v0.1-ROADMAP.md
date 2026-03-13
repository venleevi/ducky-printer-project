# Roadmap

## Milestone 1: POC (v0.1.0)

### Phase 1: Print files from USB folder
Build core functionality to detect and print files from the USB stick folder to the thermal printer.

**Goal:** Python script that can read files from `/GEN26_BILLPRINTER/` and send them to the Citizen CT-S310IIEBK printer via USB.

**Scope:**
- USB printer detection and connection
- File reading from USB stick folder
- Print job execution
- Basic error handling

**Plans:** 4 plans

Plans:
- [x] 01-01-PLAN.md — Foundation setup (requirements, file handler, USB permissions docs)
- [x] 01-02-PLAN.md — Core implementation (printer module, test infrastructure)
- [x] 01-03-PLAN.md — CLI integration (entry point, full test suite)
- [x] 01-04-PLAN.md — Hardware verification (manual testing with real printer)

### Phase 2: Testing and validation
Test the POC with real print jobs and validate output quality.

**Goal:** Verify the system works reliably with various file types and content.

**Scope:**
- Test with sample receipts
- Validate print formatting
- Document printer behavior
- Error scenario testing
