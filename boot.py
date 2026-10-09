# boot.py -- run on boot-up
import network

# Initialize WiFi hardware driver early
try:
    _sta = network.WLAN(network.STA_IF)
    _sta.active(True)
except Exception:
    pass

import main
main.main()
