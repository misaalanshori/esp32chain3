# state.py - System state container
import time
import gc
import machine

class SystemState:
    def __init__(self):
        self.boot_time = time.ticks_ms()
        self.active_app = "Menu"
        self.menu_index = 1
        self.wifi_manager = None
        self.sensor_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "temp": 0.0,
            "active": False,
        }

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
            },
            "sensors": self.sensor_data,
        }

# Global singleton
system_state = SystemState()
