# Official Procedure to Change SW1-3 on Citizen CT-S310II

**Source**: CT-S310II User Manual (Page 39) - "Manual Setting Of Memory Switches"

---

## Quick Setting Mode (OFFICIAL METHOD)

### Step 1: Enter Quick Setting Mode

1. **Load paper** (make sure paper is installed)
2. **Press FEED button 3 times** quickly
3. **Close paper cover**
4. Printer enters **Memory Switch Quick Setting Mode**
5. Printer prints: "Model" and current selection

### Step 2: Navigate to SW1-3

6. **Press FEED button** repeatedly
7. Each press prints the next setting
8. Keep pressing until you see something like:
   - "SW1-3: Busy Condition" or
   - "SW1-3: Top Margin" or
   - Current value shown

### Step 3: Change the Value

9. When you reach SW1-3, **keep pressing FEED**
10. Each press cycles through available values:
    - OFF → ON → OFF → ON...
11. **Stop when you see ON** (or the value you want)

### Step 4: Save the Setting

12. **Hold FEED button for at least 2 seconds**
13. The setting is saved
14. Printer may print "Saved" or beep

### Step 5: Exit and Apply

15. **Turn printer OFF**
16. **Turn printer ON**
17. Settings are now active

---

## Alternative Method: Self-Test Configuration

If Quick Setting Mode doesn't work:

### Enter Self-Test Mode

1. **Turn printer OFF**
2. **Press and hold FEED button**
3. **Turn printer ON** (keep holding FEED)
4. **Hold for about 1 second** then release
5. Printer prints self-test with all current settings

### View Current Settings

Look at the printout for SW1 row:
```
│ SW1 │ OFF │ OFF │ OFF │ OFF │ OFF │ OFF │ OFF │ OFF │
                    ↑
                 SW1-3 (should be OFF currently)
```

### Change Settings (Method varies by firmware)

After self-test, some firmware versions allow:
- Pressing FEED to enter configuration mode
- Cycling through settings with FEED
- Toggling values with FEED
- Holding FEED to save

**Note**: Exact procedure may vary slightly by firmware version.

---

## Verification

After changing SW1-3 to ON:

1. **Do another self-test** (HOLD FEED → Turn ON)
2. **Check printout** - SW1-3 should now show **ON**
3. **Test print**: `python test_margins.py`
4. **Measure top margin** - should be ~1mm (was 11mm)

---

## Expected Result

- **SW1-3 = OFF**: 11mm top margin (wasteful)
- **SW1-3 = ON**: 1mm top margin (optimized)
- **Savings**: 10mm per print! 🎉

---

## Sources

- [Manual Setting Of Memory Switches - Citizen CT-S310II User Manual (Page 39)](https://www.manualslib.com/manual/467787/Citizen-Ct-S310ii.html?page=39)
- [Citizen CT-S310II User Manual (Page 46)](https://www.manualslib.com/manual/1076404/Citizen-Ct-S310ii.html?page=46)
- [Official CT-S310II User Manual PDF](https://www.citizen-systems.co.jp/cms/c-s/en/printer/download/document-user-pos_mobile/CT-S310II_UM_130_EN.pdf)
- [CT-S310II Manuals and Datasheets](https://www.citizen-systems.com/en/support/manuals-and-datasheets/CT-S310II)
