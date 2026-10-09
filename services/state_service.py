# services/state_service.py - Central System State & Buffer Management Service
import time
import gc
import machine

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
        self.fft_bytes = bytearray(100)
        self.fft_active_len = 100
        self.fft_seq = 0
        # FFT Configurable Parameters
        self.fft_size = 64
        self.fft_sample_delay = 3
        self.fft_gain = 1.0
        self.fft_window = "hann"
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

    def set_fft_data(self, energy, mag_x, mag_y, mag_z, half_n=32):
        self.fft_seq = (self.fft_seq + 1) & 0xFF
        b = self.fft_bytes
        b[0] = self.fft_seq
        energy_scaled = int(energy * self.fft_gain)
        b[1] = min(255, energy_scaled // (240 if half_n == 32 else 120))
        b[2] = half_n
        b[3] = self.fft_sample_delay

        div = max(1.0, 30.0 / self.fft_gain)
        for i in range(half_n):
            b[4 + i] = min(255, int(mag_x[i] / div))
            b[4 + half_n + i] = min(255, int(mag_y[i] / div))
            b[4 + 2 * half_n + i] = min(255, int(mag_z[i] / div))
        self.fft_active_len = 4 + 3 * half_n

    def get_fft_raw(self):
        return memoryview(self.fft_bytes)[:self.fft_active_len]

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
