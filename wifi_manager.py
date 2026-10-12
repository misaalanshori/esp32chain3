# wifi_manager.py - Multi WiFi Manager with Auto-Reconnect, Auto-Switch, and Auto-AP
import network
import asyncio
import time
from container import ioc

try:
    from secrets import WIFI_NETWORKS
except ImportError:
    WIFI_NETWORKS = []

class WiFiManager:
    def __init__(self, networks=None, ap_ssid="ESP32-Chain3"):
        self.known_networks = networks if networks is not None else WIFI_NETWORKS
        self.ap_ssid = ap_ssid
        self.sta = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)

        self.status = "INITIALIZING"
        self.mode = "NONE"
        self.current_ssid = None
        self.ip = "0.0.0.0"
        self.netmask = "0.0.0.0"
        self.gateway = "0.0.0.0"
        self.dns = "0.0.0.0"
        self.rssi = 0
        try:
            self.mac = ":".join("{:02X}".format(b) for b in self.sta.config("mac"))
        except Exception:
            self.mac = "00:00:00:00:00:00"

        self.scan_results = []
        self.reconnect_count = 0
        self._running = True

        # Attach to StateService via IoC if available
        if ioc.has("state"):
            ioc.resolve("state").wifi_manager = self

    def get_state(self):
        if self.sta.isconnected():
            try:
                self.rssi = self.sta.status("rssi")
            except Exception:
                pass
        return {
            "status": self.status,
            "mode": self.mode,
            "ssid": self.current_ssid,
            "ip": self.ip,
            "netmask": self.netmask,
            "gateway": self.gateway,
            "dns": self.dns,
            "rssi": self.rssi,
            "mac": self.mac,
            "reconnect_count": self.reconnect_count,
            "known": [s for s, _ in self.known_networks],
            "scanned": self.scan_results[:10],
        }

    def _update_ip_info(self, iface):
        try:
            cfg = iface.ifconfig()
            self.ip = cfg[0]
            self.netmask = cfg[1]
            self.gateway = cfg[2]
            self.dns = cfg[3]
        except Exception:
            pass

    def scan(self):
        self.sta.active(True)
        try:
            raw = self.sta.scan()
            results = []
            for item in raw:
                ssid = item[0].decode("utf-8", "ignore")
                rssi = item[3]
                auth = item[4]
                if ssid:
                    results.append({"ssid": ssid, "rssi": rssi, "secure": (auth != 0)})
            self.scan_results = sorted(results, key=lambda x: x["rssi"], reverse=True)
            return self.scan_results
        except Exception as e:
            print("WiFi scan error:", e)
            return []

    async def _try_connect_sta(self, ssid, password, timeout_s=9):
        self.status = "CONNECTING"
        self.current_ssid = ssid
        self.sta.active(True)
        self.sta.connect(ssid, password)

        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < (timeout_s * 1000):
            if self.sta.isconnected():
                self.status = "CONNECTED"
                self.mode = "STA"
                self._update_ip_info(self.sta)
                try:
                    self.rssi = self.sta.status("rssi")
                except Exception:
                    self.rssi = 0
                if self.ap.active():
                    self.ap.active(False)
                return True
            await asyncio.sleep_ms(250)
        return False

    def _enable_ap(self):
        self.status = "AP_MODE"
        self.mode = "AP"
        self.current_ssid = self.ap_ssid
        self.ap.active(True)
        try:
            self.ap.config(essid=self.ap_ssid)
        except Exception:
            pass
        self._update_ip_info(self.ap)
        self.rssi = 0

    async def run_loop(self):
        # Yield to let UI render immediately upon boot
        await asyncio.sleep_ms(100)
        fail_cycles = 0

        while self._running:
            # 1. Connected in STA mode
            if self.sta.isconnected():
                self.status = "CONNECTED"
                self.mode = "STA"
                self._update_ip_info(self.sta)
                try:
                    self.rssi = self.sta.status("rssi")
                except Exception:
                    pass
                fail_cycles = 0
                await asyncio.sleep(3)
                continue

            # 2. Try direct connect to known networks first (fast, non-blocking)
            connected = False
            for ssid, pwd in self.known_networks:
                if await self._try_connect_sta(ssid, pwd, timeout_s=10):
                    connected = True
                    break

            if connected:
                fail_cycles = 0
                continue

            # 3. If direct connect failed, scan available networks
            self.mode = "NONE"
            self.reconnect_count += 1
            self.status = "SCANNING"
            await asyncio.sleep_ms(50)
            scanned = self.scan()
            scanned_ssids = [item["ssid"] for item in scanned]

            for ssid, pwd in self.known_networks:
                if ssid in scanned_ssids:
                    if await self._try_connect_sta(ssid, pwd, timeout_s=8):
                        connected = True
                        break

            if connected:
                fail_cycles = 0
                continue

            # 4. Fallback to AP mode after repeated failures
            fail_cycles += 1
            if fail_cycles >= 2:
                self._enable_ap()
                for _ in range(12):
                    if not self._running:
                        break
                    await asyncio.sleep(2)
            else:
                await asyncio.sleep(3)
