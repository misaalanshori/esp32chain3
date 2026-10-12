# main.py - Application Bootstrap & Unified Asynchronous Engine
import asyncio

from container import ioc
from services import StateService, MatrixService, IMUService, AppManager
from wifi_manager import WiFiManager
from menu import Menu
from webserver import WebServer
from controllers import SystemController, AppController, StreamController
from apps import REGISTERED_APPS

def bootstrap_container():
    """Initializes IoC container, services, controllers, and applications."""
    # 1. Register Core Domain Services
    state = ioc.register_singleton("state", StateService())
    matrix = ioc.register_singleton("matrix", MatrixService(width=6, height=5, pin_id=7, brightness=0.3))
    imu = ioc.register_singleton("imu", IMUService(pwr_pin=2, scl_pin=4, sda_pin=3))
    state.matrix_service = matrix

    wifi = ioc.register_singleton("wifi", WiFiManager())
    state.wifi_manager = wifi

    app_mgr = ioc.register_singleton("app_manager", AppManager(matrix, imu, state, button_pin=9))
    for name, handler in REGISTERED_APPS:
        app_mgr.register(name, handler)

    menu = ioc.register_singleton("menu", Menu(matrix, app_mgr, hold_ms=500))
    # Render menu digit immediately upon boot
    menu.draw_menu()

    # 2. Register WebServer & MVC Controllers
    web = ioc.register_singleton("webserver", WebServer(ioc, port=80))
    web.register_controller(SystemController(ioc))
    web.register_controller(AppController(ioc))
    web.register_controller(StreamController(ioc))

    return wifi, web, menu

async def main_async():
    wifi, web, menu = bootstrap_container()
    print("Framework initialized. Starting unified uasyncio event loop...")

    # Run background WiFi, MVC Web Server, and Physical UI Menu cooperatively
    await asyncio.gather(
        wifi.run_loop(),
        web.run_server(),
        menu.run_loop(),
    )

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
