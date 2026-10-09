# main.py - Device entrypoint and system orchestration
import machine
import neopixel
import _thread
import asyncio

from neomatrix import NeoMatrix
from menu import Menu
from wifi_manager import WiFiManager
from webserver import run_server
from state import system_state
from apps import REGISTERED_APPS, MATRIX_WIDTH, MATRIX_HEIGHT

async def _network_tasks():
    wm = WiFiManager()
    asyncio.create_task(wm.run_loop())
    await run_server(port=80)

def start_background_services():
    _thread.stack_size(14336)
    _thread.start_new_thread(lambda: asyncio.run(_network_tasks()), ())

def main():
    # 1. Start background WiFi Manager and Async Web Server
    start_background_services()

    # 2. Setup NeoPixel Matrix
    neo_pin = machine.Pin(7, machine.Pin.OUT)
    neo_pixel = neopixel.NeoPixel(neo_pin, MATRIX_WIDTH * MATRIX_HEIGHT)
    matrix = NeoMatrix(MATRIX_WIDTH, MATRIX_HEIGHT, neo_pixel)
    matrix.set_brightness(0.3)
    system_state.matrix = matrix

    # 3. Setup Menu and register applications
    menu = Menu(matrix, btn_pin=9, hold_ms=600)
    for name, handler in REGISTERED_APPS:
        menu.register(name, handler)

    menu.run()

if __name__ == "__main__":
    main()
