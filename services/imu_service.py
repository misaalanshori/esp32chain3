# services/imu_service.py - MPU6050 6-DoF IMU Sensor Driver Service
import machine
import time

class IMUService:
    def __init__(self, pwr_pin=2, scl_pin=4, sda_pin=3):
        self.pwr_pin = pwr_pin
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self._imu = None
        self._i2c = None

    def get_imu(self):
        if self._imu is None:
            try:
                from MPU6050 import MPU6050
                pwr = machine.Pin(self.pwr_pin, machine.Pin.OUT)
                pwr.value(1)
                time.sleep_ms(30)
                self._i2c = machine.SoftI2C(scl=machine.Pin(self.scl_pin), sda=machine.Pin(self.sda_pin), freq=400000)
                self._imu = MPU6050(i2c=self._i2c)
            except Exception as e:
                print("IMU Service Error:", e)
                return None
        return self._imu

    def read_raw_accel_into(self, buf6):
        """Read 6 raw bytes from MPU6050 register 0x3B directly at 400kHz."""
        if self._i2c is None:
            self.get_imu()
        if self._i2c is not None:
            self._i2c.readfrom_mem_into(0x68, 0x3B, buf6)
