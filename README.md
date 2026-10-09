# ESP32-C3 Pin Mapping

## Peripherals & Pins

| Peripheral | Function / Signal | ESP32-C3 GPIO | Notes |
|------------|-------------------|---------------|-------|
| **NeoPixel Matrix** | DIN (Data) | `GPIO 7` | 6x5 matrix (30 LEDs), serpentine layout |
| **Boot Button** | Input (Active LOW) | `GPIO 9` | Short press: cycle apps, Long press: open app / exit |
| **MPU6050 (GY-521)** | VCC / Power Control | `GPIO 2` | Output HIGH to power sensor |
| | SDA | `GPIO 3` | SoftI2C (`mpu = MPU6050(i2c=...)`) |
| | SCL | `GPIO 4` | SoftI2C |
| | I2C Address | `0x68` | Default address |

## Menu System (`menu.py`)

- **Short press (< 600ms)**: Cycles through registered apps (shows digit 1..9 in 3x5 font).
- **Hold (600ms)**: Column 5 fills up as a hold meter. When full, flashes and opens the app.
- **Exit app (optional)**: Holding BOOT for > 500ms exits back to the menu if the app uses `check_exit(btn)`.

### Registered Apps:
1. `Rainbow`: Animated RGB wave on matrix.
2. `JedagJedug`: Color wheel cycle across the strip.
3. `BubbleLevel`: Interactive tilt level using MPU6050.

## Multi WiFi Manager (`wifi_manager.py`)

- **Auto-connect & Switch**: Priority-based connecting across configured SSIDs in `secrets.py`.
- **Auto-reconnect**: Detects dropped connections and restores STA link.
- **Auto-AP fallback**: Starts `ESP32-Chain3` AP (`192.168.4.1`) if no known networks are reachable, and periodically scans to resume STA mode.

### Setup Credentials (`secrets.py`)
Copy `secrets.py.example` to `secrets.py` (which is in `.gitignore`):
```python
WIFI_NETWORKS = [
    ("MainSSID", "MainPassword"),
    ("SecondarySSID", "SecondaryPassword"),
]
```

## Async Web Server (`webserver.py`)

Runs as a background async task on port 80 at boot.

- `GET /`: Responsive dark-mode dashboard with live status updates (RAM, WiFi, App, MPU6050 sensors, Scanned networks).
- `GET /api/state`: Full system state JSON endpoint.
- `GET /api/scan`: Trigger WiFi scan and return visible networks.

