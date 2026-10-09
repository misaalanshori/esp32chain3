# state.py - System state container
import time
import gc
import machine

# Serpentine layout indices for 6x5 matrix
INDEX_MAP = (
    0, 1, 2, 3, 4, 5,
    11, 10, 9, 8, 7, 6,
    12, 13, 14, 15, 16, 17,
    23, 22, 21, 20, 19, 18,
    24, 25, 26, 27, 28, 29,
)

class SystemState:
    def __init__(self):
        self.boot_time = time.ticks_ms()
        self.active_app = "Menu"
        self.menu_index = 1
        self.registered_apps = []
        self.wifi_manager = None
        self.matrix = None
        self.screen_bytes = bytearray(90)
        self.sensor_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "temp": 0.0,
            "active": False,
        }

    def set_active_app(self, name):
        self.active_app = name

    def set_registered_apps(self, apps_list):
        self.registered_apps = [{"id": i + 1, "name": name} for i, (name, _) in enumerate(apps_list)]

    def set_menu_index(self, idx):
        self.menu_index = idx

    def set_sensor(self, x, y, z, temp=None):
        self.sensor_data["x"] = round(float(x), 2)
        self.sensor_data["y"] = round(float(y), 2)
        self.sensor_data["z"] = round(float(z), 2)
        if temp is not None:
            self.sensor_data["temp"] = round(float(temp), 1)
        self.sensor_data["active"] = True

    def get_screen_raw(self):
        if not self.matrix:
            return self.screen_bytes
        try:
            np_buf = self.matrix.neopixel.buf
            br = getattr(self.matrix, "brightness", 1.0)
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
        if not self.matrix:
            return ["#000000"] * 30
        try:
            np_buf = self.matrix.neopixel.buf
            br = getattr(self.matrix, "brightness", 1.0)
            scale = (1.0 / br) if (br > 0.05) else 1.0

            pixels = []
            for idx in INDEX_MAP:
                off = idx * 3
                g = np_buf[off]
                r = np_buf[off + 1]
                b = np_buf[off + 2]
                rn = min(255, int(r * scale))
                gn = min(255, int(g * scale))
                bn = min(255, int(b * scale))
                pixels.append("#{:02x}{:02x}{:02x}".format(rn, gn, bn))
            return pixels
        except Exception:
            return ["#000000"] * 30

    def get_summary(self):
        uptime_s = time.ticks_diff(time.ticks_ms(), self.boot_time) // 1000
        free = gc.mem_free()
        alloc = gc.mem_alloc()
        wifi = self.wifi_manager.get_state() if self.wifi_manager else {
            "status": "NOT_STARTED",
            "mode": "NONE",
            "ssid": None,
            "ip": "0.0.0.0",
            "rssi": 0,
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

# Global singleton
system_state = SystemState()
