# ESP32-C3 Pin Mapping

## Peripherals & Pins

| Peripheral | Function / Signal | ESP32-C3 GPIO | Notes |
|------------|-------------------|---------------|-------|
| **NeoPixel Matrix** | DIN (Data) | `GPIO 7` | 6x5 matrix (30 LEDs), serpentine layout |
| **MPU6050 (GY-521)** | VCC / Power Control | `GPIO 2` | Output HIGH to power sensor |
| | SDA | `GPIO 3` | SoftI2C (`mpu = MPU6050(i2c=...)`) |
| | SCL | `GPIO 4` | SoftI2C |
| | I2C Address | `0x68` | Default address |
