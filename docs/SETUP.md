# USB Thermal Printer Setup Guide

This guide covers setting up USB permissions and dependencies for the Citizen CT-S310IIEBK thermal printer on Raspberry Pi.

## Prerequisites

- **Hardware:** Raspberry Pi 3B+ or newer
- **OS:** Raspberry Pi OS (Debian-based)
- **Printer:** Citizen CT-S310IIEBK thermal printer connected via USB
- **Software:** Python 3.7+ installed

## 1. Install Dependencies

### System Dependencies

The system needs `libusb` for USB communication with the printer:

```bash
# Update package lists
sudo apt-get update

# Install libusb (USB communication library) and pip
sudo apt-get install -y libusb-1.0-0 python3-pip python3-venv
```

### Python Dependencies

Create a virtual environment and install Python packages:

```bash
# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

This installs:
- `python-escpos` - ESC/POS thermal printer control library
- `pytest` - Testing framework
- `pytest-mock` - Mock USB hardware for testing

The `python-escpos` library automatically includes:
- `pyusb` - USB backend for device communication
- `Pillow` - Image processing support

## 2. USB Permissions Setup

> **⚠️ CRITICAL:** USB permission configuration is required for non-root printer access. This is the most common failure point.

### Step 1: Find Printer USB ID

Connect the printer via USB and identify its vendor/product ID:

```bash
lsusb
```

Example output:
```
Bus 001 Device 005: ID 2730:0fff Citizen Systems Thermal Printer
```

In this example:
- **Vendor ID:** `2730` (Citizen Systems)
- **Product ID:** `0fff` (specific model)

### Step 2: Create udev Rule

Create a udev rule to grant non-root USB access. Choose **Option A** (recommended) or **Option B**:

#### Option A: Generic Printer Class Rule (Recommended)

This rule applies to any USB printer device (class 7):

```bash
sudo nano /etc/udev/rules.d/99-thermal-printer.rules
```

Add this line:
```
SUBSYSTEM=="usb", ATTR{bInterfaceClass}=="07", MODE="0666"
```

**Pros:** Works with any USB printer, survives firmware updates
**Cons:** Less specific (affects all USB printers)

#### Option B: Specific Vendor/Product ID Rule

This rule applies only to your specific printer model:

```bash
sudo nano /etc/udev/rules.d/99-thermal-printer.rules
```

Add this line (replace `2730` and `0fff` with your printer's IDs from Step 1):
```
SUBSYSTEM=="usb", ATTR{idVendor}=="2730", ATTR{idProduct}=="0fff", MODE="0666"
```

**Pros:** More specific and secure
**Cons:** Needs updating if printer model changes

### Step 3: Reload udev Rules

Apply the new udev rules without rebooting:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Step 4: Reconnect Printer

**Physically disconnect and reconnect** the USB cable to apply the new permissions.

### Step 5: Verify Permissions

Check that the printer device has correct permissions:

```bash
# Find printer device
ls -l /dev/usb/lp*

# Or check all USB devices
ls -l /dev/bus/usb/001/
```

Look for permissions like `crw-rw-rw-` (mode 0666) - this allows non-root read/write access.

## 3. Alternative: User Group Method

If udev rules don't work, add your user to the `lp` (line printer) group:

```bash
# Add current user to lp group
sudo usermod -aG lp $USER

# Log out and log back in for group changes to take effect
# Then verify group membership:
groups
```

You should see `lp` in the list of groups.

## 4. Troubleshooting

### "Permission denied" Errors

**Symptoms:** `PermissionError` or `usb.core.USBError: [Errno 13] Access denied`

**Solutions:**
1. Verify udev rules are created: `cat /etc/udev/rules.d/99-thermal-printer.rules`
2. Reload udev rules: `sudo udevadm control --reload-rules && sudo udevadm trigger`
3. Reconnect printer (physically unplug and replug USB)
4. Check device permissions: `ls -l /dev/usb/lp*` or `ls -l /dev/bus/usb/*/*`
5. Try the alternative user group method above

### "No printer found" Errors

**Symptoms:** `usb.core.NoBackendError` or printer not detected

**Solutions:**
1. Verify printer is powered on
2. Check USB cable is securely connected at both ends
3. Run `lsusb` to verify the printer appears in the USB device list
4. Try a different USB port on the Raspberry Pi
5. Verify `libusb-1.0-0` is installed: `dpkg -l | grep libusb`

### "Invalid endpoint address" Errors

**Symptoms:** Communication errors or data transfer failures

**Solutions:**
1. This may require specifying USB endpoints manually (covered in future plans)
2. Check `dmesg | grep usb` for USB subsystem errors
3. Try unplugging other USB devices to rule out power/bandwidth issues

### pytest Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'pytest'`

**Solutions:**
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Verify installation: `pip list | grep pytest`

## 5. Testing Connection

Once the printer setup is complete, test the connection:

```bash
# Activate virtual environment
source venv/bin/activate

# Run print job script (available in future plans)
python src/print_job.py test.txt
```

Expected output:
- Script should connect to the printer
- Read the file content
- Send print job to the printer
- Print receipt should emerge from the printer

## Additional Resources

- [python-escpos Documentation](https://python-escpos.readthedocs.io/)
- [Raspberry Pi USB Configuration](https://www.raspberrypi.org/documentation/computers/configuration.html)
- [udev Rules Writing Guide](https://wiki.archlinux.org/title/Udev)

## Next Steps

After completing this setup:
1. Run the test suite: `pytest tests/`
2. Proceed to implementing the printer module (Plan 01-02)
3. Create the CLI entry point (Plan 01-03)
4. Test with real hardware (Plan 01-04)
