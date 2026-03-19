# Ducky Printer - Installation Guide

## Prerequisites

- Raspberry Pi 3B+ running Raspberry Pi OS Bookworm
- Citizen CT-S310IIEBK thermal printer (USB)
- Physical button or toggle switch
- Python 3.11+

## Installation Steps

### 1. Install System Dependencies

```bash
# Install lgpio (required for GPIO on Bookworm)
sudo apt-get update
sudo apt-get install -y python3-lgpio python3-full git
```

### 2. Clone and Setup Project

```bash
cd /home/admin
git clone <your-repo> ducky-printer-project
cd ducky-printer-project

# Create virtual environment with system site packages (for lgpio)
python3 -m venv venv --system-site-packages

# Install dependencies
./venv/bin/pip install -r requirements.txt
```

### 3. Blacklist usblp Kernel Module

```bash
# Copy blacklist configuration
sudo cp usblp-blacklist.conf /etc/modprobe.d/

# Unload usblp if currently loaded
sudo modprobe -r usblp

# Verify blacklist
lsmod | grep usblp  # Should return nothing
```

### 4. Configure the Service

```bash
# Create config file from example
cp config.example.yaml config.yaml

# Edit configuration (optional - defaults work for GPIO 17)
nano config.yaml
```

**Default Configuration:**
- GPIO Pin: 17 (Physical Pin 11)
- Trigger Mode: press (momentary button)
- Cooldown: 2 seconds
- Source Folder: print_files/

### 5. Wire the Button

**Button Wiring:**
- Connect one side to **Pin 11** (GPIO 17)
- Connect other side to **Pin 9** (Ground)

### 6. Create Print Files Folder

```bash
mkdir -p print_files

# Add some test files
echo "Hello from Ducky Printer!" > print_files/test.txt
```

### 7. Install systemd Service

```bash
# Copy service file
sudo cp ducky-printer.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable ducky-printer.service

# Start service now
sudo systemctl start ducky-printer.service
```

## Verify Installation

### Check Service Status

```bash
sudo systemctl status ducky-printer.service
```

### View Logs

```bash
# Live logs
sudo journalctl -u ducky-printer.service -f

# Recent logs
sudo journalctl -u ducky-printer.service -n 50
```

### Test Button

Press the button connected to GPIO 17. You should see:
- Logs showing "Print triggered"
- A random file printing from print_files/
- Cooldown preventing immediate re-trigger

## Troubleshooting

### Service Won't Start

```bash
# Check for errors
sudo journalctl -u ducky-printer.service -n 100

# Common issues:
# - Missing dependencies: ./venv/bin/pip install -r requirements.txt
# - Wrong permissions: Check files are owned by admin user
# - Config errors: Check config.yaml syntax
```

### No GPIO Detection

```bash
# Verify lgpio is installed
python3 -c "import lgpio; print('lgpio OK')"

# Check if running on actual Pi (not via SSH simulation)
# GPIO requires physical hardware
```

### Printer Not Found

```bash
# Check USB connection
lsusb | grep Citizen

# Verify usblp is blacklisted
lsmod | grep usblp  # Should return nothing

# Check USB permissions
ls -l /dev/usb/
```

### Config Hot-Reload Not Working

```bash
# Check watchdog is installed
./venv/bin/pip list | grep watchdog

# Edit config.yaml while service is running
# Check logs for "Config reloaded" message
sudo journalctl -u ducky-printer.service -f
```

## Stopping the Service

```bash
# Stop service
sudo systemctl stop ducky-printer.service

# Disable auto-start on boot
sudo systemctl disable ducky-printer.service
```

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop ducky-printer.service
sudo systemctl disable ducky-printer.service

# Remove service file
sudo rm /etc/systemd/system/ducky-printer.service

# Remove blacklist
sudo rm /etc/modprobe.d/usblp-blacklist.conf

# Reload usblp (if needed)
sudo modprobe usblp

# Remove project
rm -rf /home/admin/ducky-printer-project
```

## Configuration Reference

See `config.example.yaml` for all available options:

- `gpio_pin`: GPIO pin number (BCM numbering, 2-27)
- `trigger_mode`: "press" (button) or "switch" (toggle)
- `cooldown_seconds`: Minimum time between prints
- `source_folder`: Folder containing printable files
- `switch_direction`: "both", "on_only", or "off_only" (switch mode only)

## Support

For issues, check:
1. Service logs: `sudo journalctl -u ducky-printer.service -f`
2. Config validation: Edit config.yaml and watch logs
3. Hardware: Verify button wiring and printer USB connection
