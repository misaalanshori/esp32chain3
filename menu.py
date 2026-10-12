# menu.py - Asynchronous, Non-Blocking Menu Engine
import time
import asyncio
from services import AppContext
from apps.utils import DIGITS, FONT_3x5

APP_COLORS = (
    0x07FF, 0x07E0, 0xFFE0, 0xF81F, 0xFD20, 0x041F,
    0xF800, 0xFFFF, 0xFC18, 0xFA60, 0x87E0, 0x781F, 0xFD00
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

    async def scroll_marquee(self, text, color, speed_ms=120):
        """Scrolls text horizontally. Returns True if cancelled by tap."""
        btn = self.app_manager.button
        col_bits = [[] for _ in range(5)]
        for y in range(5):
            col_bits[y].extend([0] * 6)
        for ch in text.upper():
            glyph = FONT_3x5.get(ch, FONT_3x5.get(' ', (0, 0, 0, 0, 0)))
            for y in range(5):
                r = glyph[y]
                col_bits[y].extend([(r >> 2) & 1, (r >> 1) & 1, r & 1, 0])
        for y in range(5):
            col_bits[y].extend([0] * 6)

        total_cols = len(col_bits[0])
        for col_idx in range(total_cols - 5):
            # Single tap cancels marquee immediately
            if btn.value() == 0:
                while btn.value() == 0:
                    await asyncio.sleep_ms(10)
                await asyncio.sleep_ms(40)
                return True

            if self.app_manager.preempt_request is not None:
                return True

            self.matrix.fill(0)
            for x in range(6):
                src_x = col_idx + x
                for y in range(5):
                    if col_bits[y][src_x]:
                        self.matrix.pixel(x, y, color)
            self.matrix.show()
            await asyncio.sleep_ms(speed_ms)

        return False

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
                    # Short press: Check for double tap
                    if time.ticks_diff(time.ticks_ms(), t0) > 25:
                        while btn.value() == 0:
                            await asyncio.sleep_ms(10)
                        await asyncio.sleep_ms(30)

                        # Wait up to 250ms for a second press
                        double_tapped = False
                        t_rel = time.ticks_ms()
                        while time.ticks_diff(time.ticks_ms(), t_rel) < 250:
                            if btn.value() == 0:
                                double_tapped = True
                                break
                            await asyncio.sleep_ms(15)

                        if double_tapped:
                            while btn.value() == 0:
                                await asyncio.sleep_ms(10)
                            await asyncio.sleep_ms(30)

                            # DOUBLE TAP: Scroll app name marquee
                            name = self.app_manager.catalog[self.current][0]
                            col = APP_COLORS[self.current % len(APP_COLORS)]
                            await self.scroll_marquee(name, col)
                            # Return to menu on the SAME app item
                            self.draw_menu()
                        else:
                            # SINGLE TAP: Advance to next app item
                            self.current = (self.current + 1) % len(self.app_manager.catalog)
                            self.draw_menu()

            await asyncio.sleep_ms(25)
