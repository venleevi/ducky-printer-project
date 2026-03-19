# Citizen CT-S310IIEBK Margin Research Summary

**Date**: 2026-03-19
**Printer Model**: Citizen CT-S310IIEBK (80mm thermal receipt printer)
**Issue**: Excessive vertical whitespace at top (~2-5mm) and bottom (~5-15mm) of prints

---

## 1. TOP MARGIN SPECIFICATIONS (FOUND!)

### Memory Switch Setting: MSW8-3
- **Default Top Margin**: **11mm**
- **Configurable Values**: 1mm, 3mm, 4mm, 5mm, 6mm, 7mm, 8mm, 9mm, 10mm
- **Location**: Memory Switch 8-3 (MSW8-3)

**This is the hardware-enforced top margin that explains the ~2-5mm+ whitespace at the top of prints!**

### How to Change Top Margin
The top margin can be reduced via memory switch configuration. The minimum is **1mm**.

---

## 2. LINE FEED / SPACING SPECIFICATIONS

### Default Line Feed Rates (CT-S310II)
- **MSW 5-2 OFF**: Approx. 4.23mm (1/6 inch)
- **MSW 5-2 ON**: Approx. 3.75mm

### ESC/POS Commands for Vertical Spacing

#### ESC J n - Print and feed paper in minimum pitch
```
Code: <1B>H<4A>H<n>
Range: 0≤n≤255
```
- Prints data in buffer and feeds paper by [n×basic calculation pitch] inches
- Does NOT change the line feed width set by ESC 2 or ESC 3
- Maximum settable line feed width: 1016mm (40 inches)

#### ESC d n - Print and feed n lines
```
Code: <1B>H<64>H<n>
Range: 0≤n≤255
```
- Prints data in buffer and feeds paper forward by n lines
- Same result as transmitting LF n times continuously

#### ESC 2 - Set line feed rate to 1/6 inch
```
Code: <1B>H<32>H
Default: 4.23mm (1/360 inches for CT-S310II)
```

#### ESC 3 n - Set line feed rate of minimum pitch
```
Code: <1B>H<33>H<n>
Range: 0≤n≤255
```
- Sets the line feed width per line to [n×basic calculation pitch] inches
- Default CT-S310II: Approx. 4.23mm (MSW 5-2 OFF) or 3.75mm (MSW 5-2 ON)
- Maximum settable line feed width: 1016mm (40 inches)

---

## 3. HORIZONTAL MARGIN / PRINT AREA

### GS L nL nH - Set left margin
```
Code: <1D>H<4C>H<nL><nH>
Range: 0≤nL≤255, 0≤nH≤255
```
- Sets left margin: [(nL+nH×256)×basic calculation pitch] inches
- Default: nL=0, nH=0 (no left margin)
- Only works when entered at beginning of a line

### GS W nL nH - Set print area width
```
Code: <1D>H<57>H<nL><nH>
Range: 0≤nL≤255, 0≤nH≤255
```
- Sets print area width: [(nL+nH×256)×basic calculation pitch] inches
- For 80mm paper with CT-S310II: 72mm (576 dots) typical printable width

**Default Print Width Settings (80mm paper)**:
| Paper Width | Print Width | nL  | nH | Model              |
|-------------|-------------|-----|----|--------------------|
| 80mm        | 72mm (576)  | 64  | 2  | CT-S310II          |
| 80mm        | 80mm (640)  | 128 | 2  | CT-S2000/CT-S801   |
| 80mm        | 68.25mm(546)| 34  | 2  | CT-S310II variants |
| 80mm        | 64mm (512)  | 0   | 2  | CT-S310II variants |

---

## 4. BOTTOM MARGIN / PAPER CUTTING

### Bottom Margin Context
- Bottom margin is typically related to paper cutting position
- The cutter position is fixed in hardware (~13-15mm from print head typically)
- Additional feeding after print completion is controlled by:
  - Paper sensor settings (MSW2-8: PNE Sensor)
  - Cut position settings
  - Feed & cut commands (ESC i, ESC m, GS V)

### Cutter Commands
- **ESC i** - Full cut
- **ESC m** - Partial cut
- **GS V m** - Cutting the paper (with modes)

The bottom whitespace is likely a combination of:
1. Paper feed needed to reach the cutter blade (~13-15mm)
2. Any post-print line feeds in your code
3. Paper sensor behavior (MSW2-8)

---

## 5. MEMORY SWITCH SETTINGS (CT-S310)

### Key Memory Switches for Margins

| Switch  | Setting        | OFF           | ON                |
|---------|----------------|---------------|-------------------|
| MSW2-5  | Resume at PE   | • Next        | Top               |
| MSW4-3  | FEED&CUT at TOF| Invalid       | • Valid           |
| MSW8-3  | **Top Margin** | **11mm**      | **Variable 1-10mm**|
| MSW8-4  | Line Gap Reduce| Invalid       | 3/4, 2/3, 1/2, 1/3, 1/4, 1/5 ALL|

**MSW8-3 is the critical setting for top margin!**

---

## 6. BIT IMAGE PRINTING DETAILS

### ESC * m n1 n2 [d] k - Specify bit image mode
For 80mm CT-S310II (72mm print width = 576 dots):

| m  | Mode                  | Vertical | Horizontal | Width for 80mm |
|----|-----------------------|----------|------------|----------------|
| 0  | 8 dot single density  | 67dpi    | 101dpi     | 416 dots       |
| 1  | 8 dot double density  | 67dpi    | 203dpi     | 832 dots       |
| 32 | 24 dot single density | 203dpi   | 101dpi     | 416 dots       |
| 33 | 24 dot double density | 203dpi   | 203dpi     | 832 dots       |

### GS v 0 m xL xH yL yH d1...dk - Raster bit image
This is what python-escpos likely uses with `impl="bitImageColumn"`:
- More efficient than ESC *
- Supports rotation and sizing
- Print start position can be set with HT, ESC $, ESC \, GS L

**Note**: The raster bit image is only valid when no print data is present in the print buffer at STANDARD MODE selection.

---

## 7. PYTHON-ESCPOS ISSUES & WORKAROUNDS

### Common Issues with CT-S310IIEBK
1. **Endpoint Configuration Error**
   - Workaround: Explicitly specify USB endpoints
   ```python
   from escpos import printer
   p = printer.Usb(0x2730, 0x200f, 0, 0x81, 0x02)
   ```
   - Vendor ID: `0x2730`
   - Product ID: `0x200f`
   - Input Endpoint: `0x81`
   - Output Endpoint: `0x02`

2. **USB Timeout Errors**
   - Use `set_sleep_in_fragment()` method to add delays between print fragments

3. **Printer Profile**
   - CT-S310II models listed in supported printers
   - May not have exact profile; uses generic ESC/POS commands

---

## 8. THERMAL PRINTER HARDWARE LIMITATIONS

### General 80mm Thermal Printer Constraints
- **Typical printable width**: 72mm on 80mm paper (not full 80mm)
- **Hardware margins**: Most thermal printers have ~3-5mm minimum side margins
- **Top/bottom margins**: Hardware-enforced for mechanical reasons:
  - Top: Paper feed mechanism (CT-S310II default: **11mm**)
  - Bottom: Distance to cutter blade (~13-15mm typical)

### Industry Standards
- Receipt printers prioritize speed over margin minimization
- Paper-saving features (like CT-S310II's "delete top margin" via MSW8-3) can reduce but not eliminate margins
- Minimum top margin on CT-S310II: **1mm** (via MSW8-3 configuration)

---

## 9. RECOMMENDATIONS FOR YOUR DUCKY PRINTER PROJECT

### Immediate Actions to Reduce Vertical Whitespace

1. **Configure Top Margin via Memory Switch MSW8-3**
   - Current: 11mm (default)
   - Target: 1mm (minimum) or 3-5mm (reasonable)
   - **This will eliminate most of your top whitespace issue**

2. **Check Your Code for Extra Line Feeds**
   - Review print commands for unnecessary `\n` or LF characters
   - Check if `paper feed after print` is enabled in python-escpos settings

3. **Optimize Bottom Margin**
   - Measure actual distance to cutter: ~13-15mm is typical
   - Remove any extra paper feeds before cut command
   - Consider using partial cut instead of full cut if supported

4. **Review Current python-escpos Settings**
   ```python
   # Current settings from your summary:
   # - 8cm width, 100cm height target
   # - rotate=True
   # - impl="bitImageColumn"

   # Check for these potential issues:
   # - Extra line_spacing settings
   # - line_feed before/after image
   # - cut settings
   ```

### How to Access Memory Switches

Memory switches can typically be accessed via:
1. **Physical DIP switches** (if accessible on printer)
2. **Self-test/configuration mode** (hold button during power-on)
3. **ESC/POS commands** via GS (E pL pH fn [parameter]
4. **Utility software** from Citizen Systems

Refer to CT-S310II User Manual Section 4 (Memory Switch) for detailed instructions.

---

## 10. KEY FINDINGS SUMMARY

### Root Causes of Excessive Margins

1. **Top Margin (~2-5mm+)**
   - **Primary cause**: MSW8-3 default setting of **11mm**
   - **Solution**: Reconfigure MSW8-3 to 1mm or 3-5mm
   - **Expected improvement**: 6-10mm reduction

2. **Bottom Margin (~5-15mm)**
   - **Primary cause**: Hardware distance to cutter blade (~13-15mm)
   - **Secondary causes**:
     - Extra line feeds in code
     - Paper sensor behavior
     - Post-print feed settings
   - **Solutions**:
     - Eliminate unnecessary line feeds
     - Optimize cutter positioning
     - Review python-escpos cut commands

### Minimum Achievable Margins
- **Top**: ~1mm (hardware minimum via MSW8-3)
- **Bottom**: ~13-15mm (hardware cutter position)
- **Total vertical whitespace**: ~14-16mm minimum

### Expected vs Current
- **Current**: ~7-20mm total (top 2-5mm + bottom 5-15mm)
- **After optimization**: ~14-16mm total (top 1mm + bottom 13-15mm)
- **Potential savings**: ~4-6mm reduction in vertical whitespace

---

## SOURCES

- [Citizen CT-S310II User Manual](https://www.citizen-systems.co.jp/cms/c-s/en/printer/download/document-user-pos_mobile/CT-S310II_UM_130_EN.pdf)
- [Citizen Command Reference Manual](https://www.citizen-systems.com/resource/support/POS/Generic_Printer_Files/Command_Reference/CommandReference.pdf) - Models: CT-S310, CT-S310II, and others
- [python-escpos Documentation](https://python-escpos.readthedocs.io/en/latest/user/usage.html)
- [python-escpos GitHub Issues](https://github.com/python-escpos/python-escpos/issues)
- [Citizen ESC/POS Printers Issue #49](https://github.com/receipt-print-hq/escpos-printer-db/issues/49)
- [ESC/POS Command Reference - Star Micronics](https://www.starmicronics.com/support/Mannualfolder/escpos_cm_en.pdf)
- [Quick Receipt - How to Adjust Receipt Margins](https://www.evinco-software.com/quick-receipt/support/kb/how-to-adjust-paper-margin/)
- [80mm Thermal Receipt Printer Buying Guide - HPRT](https://www.hprt.com/Product/POS-PRINTERS/80mm-Thermal-Receipt-Printer-Buying-Guide.html)
