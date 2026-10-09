# menu.py - Asynchronous, Non-Blocking Menu Engine
import time
import asyncio
from services import AppContext

DIGITS = (
    (0b111, 0b101, 0b101, 0b101, 0b111),  # 0
    (0b010, 0b110, 0b010, 0b010, 0b111),  # 1
    (0b111, 0b001, 0b111, 0b100, 0b111),  # 2
    (0b111, 0b001, 0b111, 0b001, 0b111),  # 3
    (0b101, 0b101, 0b111, 0b001, 0b001),  # 4
    (0b111, 0b100, 0b111, 0b001, 0b111),  # 5
    (0b111, 0b100, 0b111, 0b101, 0b111),  # 6
    (0b111, 0b001, 0b001, 0b001, 0b001),  # 7
    (0b111, 0b101, 0b111, 0b101, 0b111),  # 8
    (0b111, 0b101, 0b111, 0b001, 0b111),  # 9
)

APP_COLORS = (
    0x07FF, 0x07E0, 0xFFE0, 0xF81F, 0xFD20, 0x041F,
    0xF800, 0xFFFF, 0xFC18, 0xFA60, 0x87E0, 0x781F
)

class Menu:
    def __init__(self, matrix, app_manager, hold_ms=500):
        self.matrix = matrix
        self.app_manager = app_manager
        self.hold_ms = hold_ms
        self.current = 0

    def draw_digit(self, num, color, x_off=1):
        if num < 10:
            rows = DIGITS[num % 10]
            for y, row in enumerate(rows):
                for x in range(3):
                    if (row >> (2 - x)) & 1:
                        self.matrix.pixel(x_off + x, y, color)
        else:
            for y in range(5):
                self.matrix.pixel(1, y, color)
            rows = DIGITS[num % 10]
            for y, row in enumerate(rows):
                for x in range(3):
                    if (row >> (2 - x)) & 1:
                        self.matrix.pixel(3 + x, y, color)

    def draw_menu(self, dots=0):
        self.matrix.fill(0)
        total = len(self.app_manager.catalog)
        if total == 0:
            self.matrix.show()
            return
        num = self.current + 1
        self.app_manager.state.set_menu_index(num)
        col = APP_COLORS[self.current % len(APP_COLORS)]
        self.draw_digit(num, col, x_off=1)
        meter_col = 0 if num >= 10 else 5
        for i in range(dots):
            self.matrix.pixel(meter_col, 4 - i, 0xFFFF)
        self.matrix.show()

    async def launch_app(self, idx):
        if not (0 <= idx < len(self.app_manager.catalog)):
            return
        self.current = idx
        name, handler = self.app_manager.catalog[idx]
        self.app_manager.state.set_active_app(name)
        self.matrix.fill(0)
        self.matrix.show()

        ctx = AppContext(self.matrix, self.app_manager.imu_service, self.app_manager.state, self.app_manager)
        self.app_manager.active_ctx = ctx

        try:
            await handler(ctx)
        except Exception as e:
            print(f"App '{name}' error:", e)
        finally:
            self.app_manager.active_ctx = None

        self.app_manager.state.set_active_app("Menu")

    async def run_loop(self):
        btn = self.app_manager.button
        self.draw_menu()

        while True:
            # Check preemption / remote launch request
            if self.app_manager.preempt_request is not None:
                req = self.app_manager.preempt_request
                self.app_manager.preempt_request = None
                if req == "menu" or req == 0:
                    self.draw_menu()
                else:
                    target_idx = self.app_manager.find_index(req)
                    if target_idx is not None:
                        await self.launch_app(target_idx)
                        self.draw_menu()
                        continue

            # Non-blocking physical button poll
            if btn.value() == 0:
                t0 = time.ticks_ms()
                long_pressed = False
                prev_dots = 0

                while btn.value() == 0:
                    held = time.ticks_diff(time.ticks_ms(), t0)
                    dots = min(5, (held * 5) // self.hold_ms)
                    if dots != prev_dots:
                        prev_dots = dots
                        self.draw_menu(dots=dots)

                    if held >= self.hold_ms:
                        long_pressed = True
                        break
                    await asyncio.sleep_ms(20)

                if long_pressed:
                    self.matrix.fill(0xFFFF)
                    self.matrix.show()
                    await asyncio.sleep_ms(50)
                    while btn.value() == 0:
                        await asyncio.sleep_ms(10)
                    await asyncio.sleep_ms(40)
                    await self.launch_app(self.current)
                    self.draw_menu()
                else:
                    if time.ticks_diff(time.ticks_ms(), t0) > 30:
                        self.current = (self.current + 1) % len(self.app_manager.catalog)
                        self.draw_menu()
                        while btn.value() == 0:
                            await asyncio.sleep_ms(10)
                        await asyncio.sleep_ms(40)

            await asyncio.sleep_ms(25)
