# Monitor_Pi
![Raspberry Pi](https://github.com/doglaswicht/miniecran35/blob/main/assets/gifs2/raspberry_monitor.gif)

> MonitorPi is a compact touchscreen dashboard for small devices (Raspberry Pi). It provides a simple touchscreen menu, network device scanner, system information (CPU temperature, Wi‑Fi SSID), and safe geolocation options.

This project is intended as a lightweight, offline‑friendly control panel for home labs and small embedded projects. It includes a network scanner tuned to find cameras and other local devices and a touchscreen menu optimized for small displays.

## Table of Contents

- Features
- Quick start
- Running on Raspberry Pi
- Configuration
- Network scanner details
- Security & privacy


## Features

- Touchscreen menu with GIF support and configurable buttons
- Network scanner with ARP-assisted discovery and camera detection
- Real-time network monitor displaying all connected devices
- System info view: Wi‑Fi SSID, CPU temperature, optional geolocation
- Secure defaults: geolocation disabled by default and cached safely
- Small footprint, designed to run on a Raspberry Pi with a 480×320 framebuffer

## Quick start

Clone the repository and run the touchscreen menu from the project root:

```bash
git clone https://github.com/doglaswicht/MonitorPi_Theme_Naruto MonitorPi
cd MonitorPi
# start the main menu (root may be required for framebuffer/touch access)
sudo python3 touch_menu_visual.py
```

Alternatively you can run individual modules for testing/development:

```bash
python3 -m py_compile src/modules/painelv3.py  # syntax check
sudo python3 src/network/painelip/painel_ips.py  # run network scanner
```

## Running on Raspberry Pi

1. Use a recent Raspberry Pi OS (32/64-bit Debian-based). Keep the system updated.
2. Connect the touchscreen and ensure the framebuffer device (`/dev/fb0`) and input device (`/dev/input/event*`) are available to the running user (or run with sudo).
3. Install nmap for the network scanner features:

```bash
sudo apt update
sudo apt install -y nmap
```

4. Start the main menu with root if you need direct framebuffer access:

```bash
sudo python3 touch_menu_visual.py
```

## Configuration

Project configuration is mostly inside `src/network/painelip/config.py` and a few variables in `src/modules/painelv3.py`.

- `SCAN_INTERVAL`: seconds between network scans
- `PREF_IFACES`: preferred network interfaces (e.g. `['wlan0','eth0']`)
- `ENABLE_FULL_SCAN`: if `True` scanner will use ARP-assisted discovery and check common ports

Edit the config files to adapt to your network and device.

## Network scanner details

The scanner combines multiple approaches:

- ARP table parsing to detect devices that do not respond to ping
- Optional nmap scans on a short list of common ports
- Device classification heuristics (SSH → Linux server, RDP/SMB → Windows PC, known camera ports → camera)

If a device is present in the ARP table but its ports are filtered (firewall), it will still be shown as an `ARP Host`.

## Security & privacy

- Geolocation is implemented but disabled by default. If enabled, the code uses cautious caching and HTTPS APIs.
- The network scanner runs locally and does not share local device addresses with external services by default.
- If you enable geolocation or external APIs, be aware that IP-based location can expose your public IP and approximate location.

For full details about privacy controls see `docs/SECURITY_GEOLOCATION.md` (if present).

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repo and create a feature branch.
2. Keep changes small and focused.
3. Run `python3 -m py_compile` on modified modules and fix linting if required.
4. Open a pull request describing the change and any validation steps.


---

If you want, I can also add a short `CONTRIBUTING.md`, CI example, or a minimal `requirements.txt` (if any new dependencies are needed). Tell me which one you prefer next.
