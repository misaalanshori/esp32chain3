# services.py - Domain Services & Hardware Abstraction Layer
import time
import gc
import machine
import asyncio
from neomatrix import NeoMatrix

INDEX_MAP = (
    0, 1, 2, 3, 4, 5,
    11, 10, 9, 8, 7, 6,
    12, 13, 14, 15, 16, 17,
    23, 22, 21, 20, 19, 18,
    24, 25, 26, 27, 28, 29,
)

class StateService:
    def __init__(self):
        self.boot_time = time.ticks_ms()
        self.active_app = "Menu"
        self.menu_index = 1
        self.registered_apps = []
        self.wifi_manager = None
        self.matrix_service = None
        self.screen_bytes = bytearray(90)
        self.fft_bytes = bytearray(50)
        self.fft_seq = 0
        self.sensor_data = {
            "x": 0.0, "y": 0.0, "z": 0.0, "temp": 0.0, "active": False
        }
        # Web app states
        self.paint_frames = [["#000000"] * 30]
        self.paint_speed = 200
        self.ticker_text = "HELLO ESP32"
        self.ticker_color = "#00ffff"
        self.ticker_speed = 70
        self.studio_effect = "candle"
        self.studio_color = "#ff8800"
        self.studio_speed = 40

    def set_active_app(self, name):
        self.active_app = name

    def set_menu_index(self, idx):
        self.menu_index = idx

    def set_sensor(self, x, y, z, temp=None):
        self.sensor_data["x"] = round(float(x), 2)
        self.sensor_data["y"] = round(float(y), 2)
        self.sensor_data["z"] = round(float(z), 2)
        if temp is not None:
            self.sensor_data["temp"] = round(float(temp), 1)
        self.sensor_data["active"] = True

    def set_fft_data(self, energy, mag_x, mag_y, mag_z):
        self.fft_seq = (self.fft_seq + 1) & 0xFF
        b = self.fft_bytes
        b[0] = self.fft_seq
        # Energy normalized 0..255
        b[1] = min(255, energy // 120)
        for i in range(16):
            b[2 + i] = min(255, mag_x[i] // 30)
            b[18 + i] = min(255, mag_y[i] // 30)
            b[34 + i] = min(255, mag_z[i] // 30)

    def get_fft_raw(self):
        return self.fft_bytes

    def get_screen_raw(self):
        if not self.matrix_service:
            return self.screen_bytes
        try:
            np_buf = self.matrix_service.neopixel.buf
            br = getattr(self.matrix_service, "brightness", 1.0)
            scale = (1.0 / br) if (br > 0.05) else 1.0

            out = self.screen_bytes
            out_i = 0
            for idx in INDEX_MAP:
                off = idx * 3
                g = np_buf[off]
                r = np_buf[off + 1]
                b = np_buf[off + 2]
                out[out_i] = min(255, int(r * scale))
                out[out_i + 1] = min(255, int(g * scale))
                out[out_i + 2] = min(255, int(b * scale))
                out_i += 3
            return out
        except Exception:
            return self.screen_bytes

    def get_screen_pixels(self):
        raw = self.get_screen_raw()
        pixels = []
        for i in range(0, 90, 3):
            pixels.append("#{:02x}{:02x}{:02x}".format(raw[i], raw[i+1], raw[i+2]))
        return pixels

    def get_summary(self):
        uptime_s = time.ticks_diff(time.ticks_ms(), self.boot_time) // 1000
        free = gc.mem_free()
        alloc = gc.mem_alloc()
        wifi = self.wifi_manager.get_state() if self.wifi_manager else {
            "status": "NOT_STARTED", "mode": "NONE", "ssid": None, "ip": "0.0.0.0", "rssi": 0
        }
        return {
            "system": {
                "uptime_s": uptime_s,
                "free_ram": free,
                "alloc_ram": alloc,
                "total_ram": free + alloc,
                "cpu_freq_mhz": machine.freq() // 1000000,
            },
            "wifi": wifi,
            "app": {
                "active": self.active_app,
                "menu_index": self.menu_index,
                "list": self.registered_apps,
            },
            "sensors": self.sensor_data,
            "screen": self.get_screen_pixels(),
        }

class MatrixService(NeoMatrix):
    def __init__(self, width=6, height=5, pin_id=7, brightness=0.3):
        import neopixel
        self.pin = machine.Pin(pin_id, machine.Pin.OUT)
        self.np = neopixel.NeoPixel(self.pin, width * height)
        super().__init__(width, height, self.np)
        self.set_brightness(brightness)

class IMUService:
    def __init__(self, pwr_pin=2, scl_pin=4, sda_pin=3):
        self.pwr_pin = pwr_pin
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self._imu = None

    def get_imu(self):
        if self._imu is None:
            try:
                from MPU6050 import MPU6050
                pwr = machine.Pin(self.pwr_pin, machine.Pin.OUT)
                pwr.value(1)
                time.sleep_ms(30)
                i2c = machine.SoftI2C(scl=machine.Pin(self.scl_pin), sda=machine.Pin(self.sda_pin))
                self._imu = MPU6050(i2c=i2c)
            except Exception as e:
                print("IMU Service Error:", e)
                return None
        return self._imu

class AppContext:
    """Execution context injected into every running application."""
    def __init__(self, matrix, imu_service, state_service, app_manager):
        self.matrix = matrix
        self.imu_service = imu_service
        self.state = state_service
        self.app_manager = app_manager
        self._stop = False

    def request_exit(self):
        self._stop = True

    def should_stop(self):
        return self._stop or (self.app_manager.preempt_request is not None)

    async def sleep_ms(self, ms):
        await asyncio.sleep_ms(ms)

    def get_imu(self):
        return self.imu_service.get_imu()

    def poll_action(self, btn, hold_ms=450):
        if self.should_stop():
            return "exit"
        if btn.value() == 0:
            t0 = time.ticks_ms()
            while btn.value() == 0:
                if time.ticks_diff(time.ticks_ms(), t0) >= hold_ms:
                    while btn.value() == 0:
                        time.sleep_ms(10)
                    time.sleep_ms(30)
                    return "exit"
                time.sleep_ms(10)
            time.sleep_ms(20)
            return "tap"
        return None

class AppManager:
    """Manages cooperative preemption, lifecycle, and execution of apps."""
    def __init__(self, matrix, imu_service, state_service, button_pin=9):
        self.matrix = matrix
        self.imu_service = imu_service
        self.state = state_service
        self.button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.catalog = [] # list of (name, async_coroutine_fn)
        self.current_idx = 0
        self.active_ctx = None
        self.preempt_request = None

    def register(self, name, handler):
        self.catalog.append((name, handler))
        self.state.registered_apps = [{"id": i+1, "name": n} for i, (n, _) in enumerate(self.catalog)]

    def request_switch(self, target):
        """Preempt running app and switch to target."""
        self.preempt_request = target
        if self.active_ctx:
            self.active_ctx.request_exit()

    def find_index(self, target):
        if isinstance(target, int):
            if 1 <= target <= len(self.catalog):
                return target - 1
        elif isinstance(target, str):
            for i, (name, _) in enumerate(self.catalog):
                if name.lower() == target.lower():
                    return i
        return None
