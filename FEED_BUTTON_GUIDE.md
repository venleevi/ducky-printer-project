# Citizen CT-S310II FEED Button Configuration Guide

**IMPORTANT**: The printer has NO SCREEN - it prints EVERYTHING on receipt paper!

---

## STEP 1: Enter Configuration Mode

1. **Turn printer OFF**
2. **Press and HOLD the FEED button** (the only button on the printer)
3. **Turn printer ON** (keep holding FEED!)
4. **Keep holding until printer starts printing** (you'll hear it)
5. **Release FEED button**

---

## STEP 2: What You'll See Printed

The printer will print a LONG receipt showing all current settings. It looks like this:

```
╔══════════════════════════════════════════════════════════╗
║           CITIZEN CT-S310II                              ║
║           SELF-TEST PRINT                                ║
╚══════════════════════════════════════════════════════════╝

FIRMWARE: DTxx-0xxx
DATE: 2026-03-19

MEMORY SWITCH SETTINGS:
────────────────────────────────────────────────────────────

MSW1-1: Power ON Info           OFF
MSW1-2: Buffer Size             4K bytes
MSW1-3: Busy Condition          Full
MSW1-4: Receive Error           Print ?
MSW1-5: CR mode                 Ignored
MSW1-6: Reserved                -
MSW1-7: DSR Signal              Invalid
MSW1-8: Init Signal             Valid

MSW2-1: Reserved                Fixed
MSW2-2: Auto Cutter             Valid
MSW2-3: Spool Print             Invalid
MSW2-4: Full Col Print          WaitData
MSW2-5: Resume at PE            Next
MSW2-6: Paper width             80mm
MSW2-7: Reserved                Fixed
MSW2-8: PNE Sensor              Invalid

... more settings ...

MSW8-1: Print Width             576dots
MSW8-2: Reserved                -
MSW8-3: Top Margin              11mm        ← ← ← THIS IS WHAT YOU NEED!
MSW8-4: Line Gap Reduce         Invalid

... more settings ...

BAUD RATE: 9600bps
CODE PAGE: PC437
KANJI: OFF
...

[END OF SELF-TEST]
Press FEED to enter configuration mode
```

---

## STEP 3: Enter Edit Mode

After the self-test prints:

6. **Press FEED button ONCE**
7. Printer prints: `Configuration Mode - Press FEED to cycle options`

---

## STEP 4: Navigate to Top Margin Setting

The printer will now print ONE LINE each time you press FEED:

```
[Press FEED] → Printer prints: "MSW1-1: Power ON Info [OFF]"
[Press FEED] → Printer prints: "MSW1-2: Buffer Size [4K]"
[Press FEED] → Printer prints: "MSW1-3: Busy Condition [Full]"
... keep pressing ...
[Press FEED] → Printer prints: "MSW8-1: Print Width [576]"
[Press FEED] → Printer prints: "MSW8-2: Reserved"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [11mm]" ← ← ← STOP HERE!
```

**Key points:**
- Each FEED press prints ONE setting name
- You need to find: **"MSW8-3: Top Margin [11mm]"**
- It might also be called: **"Top Margin"**, **"Paper Save"**, or **"Top Feed"**
- Look for anything with **11mm** value

---

## STEP 5: Change the Value

When you see `MSW8-3: Top Margin [11mm]` printed:

8. **Press FEED again** to cycle through values

Each press prints the NEXT value:

```
[Press FEED] → Printer prints: "MSW8-3: Top Margin [10mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [9mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [8mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [7mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [6mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [5mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [4mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [3mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [2mm]"
[Press FEED] → Printer prints: "MSW8-3: Top Margin [1mm]" ← ← ← STOP!
```

**Stop when you see `[1mm]` or `[3mm]`** (3mm is safer if you're worried)

---

## STEP 6: Save the Setting

9. **Hold FEED button for 3 seconds** (don't just press, HOLD)

Printer will print:
```
Settings Saved
MSW8-3: Top Margin = 1mm
```

Or you might see a beep or flash.

---

## STEP 7: Exit and Apply

10. **Turn printer OFF**
11. **Turn printer ON**
12. Settings are now active!

---

## STEP 8: Verify

Test the new margin:

```bash
python test_margins.py
```

Measure the top margin with a ruler. It should now be **1-3mm** instead of **11mm**!

---

## TROUBLESHOOTING

### Problem: Can't enter configuration mode (no printout)

**Solutions:**
- Make sure you **press FEED BEFORE turning power on**
- **Keep holding FEED for 5+ seconds** after turning on
- Some printers need you to hold FEED for **10 seconds**
- Try pressing FEED + turning on power **simultaneously**

---

### Problem: Self-test prints but can't enter edit mode

**Solutions:**
- After self-test, **wait 2 seconds** then press FEED
- Try pressing FEED **twice quickly**
- Look at the bottom of self-test printout for instructions

---

### Problem: Can't find MSW8-3 or Top Margin

**Alternative names to look for:**
- `Top Margin`
- `MSW8-3`
- `Paper Save`
- `Top Feed`
- `Print Start Position`
- `Feed Amount`
- Any setting showing `11mm`

**Solution:**
- Press FEED **20-30 times** to cycle through ALL settings
- Look carefully at each printed line
- The setting MUST be there somewhere

---

### Problem: Can't change the value

**Solutions:**
- After seeing `MSW8-3: Top Margin [11mm]`:
  - Try pressing FEED **once** (should print `[10mm]`)
  - Try pressing FEED **twice quickly** (toggle mode)
  - Try **holding FEED for 1 second** then releasing

---

### Problem: Can't save settings

**Solutions:**
- Try holding FEED for **5 seconds** instead of 3
- Try holding FEED for **10 seconds**
- Try pressing FEED **twice**, then holding
- Look for printed message: "Press FEED to save" or similar

---

## WHAT YOU'RE LOOKING FOR (VISUAL GUIDE)

```
════════════════════════════════════════════════════════════════
                    SELF-TEST PRINTOUT
════════════════════════════════════════════════════════════════

... lots of settings ...

MSW8-1: Print Width             576dots
MSW8-2: Reserved                -
MSW8-3: Top Margin              11mm    ← ← ← FIND THIS LINE!
MSW8-4: Line Gap Reduce         Invalid

... more settings ...

════════════════════════════════════════════════════════════════
```

**GOAL**: Change `11mm` to `1mm` or `3mm`

---

## SUMMARY

1. **Hold FEED** → **Turn ON** → Printer prints settings
2. **Find line** with `MSW8-3: Top Margin [11mm]`
3. **Press FEED** repeatedly to cycle: 11mm → 10mm → ... → 1mm
4. **Hold FEED 3 seconds** to save
5. **Power cycle** printer
6. **Test**: `python test_margins.py`

---

## Expected Result

**Before**: Top margin ~11mm
**After**: Top margin ~1-3mm
**Savings**: ~8-10mm per print! 🎉

---

Need help? Run: `python src/configure_printer_margins.py`
