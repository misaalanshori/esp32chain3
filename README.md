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
