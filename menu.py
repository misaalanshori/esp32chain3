# menu.py - Lightweight menu system for 6x5 NeoMatrix
import time
import machine

# 3x5 font bitmaps for digits 0-9 (5 rows x 3 bits wide)
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
    0x07FF,  # 1: Cyan
    0x07E0,  # 2: Green
    0xFFE0,  # 3: Yellow
    0xF81F,  # 4: Magenta
    0xFD20,  # 5: Orange
    0x041F,  # 6: Blue
    0xF800,  # 7: Red
    0xFFFF,  # 8: White
    0xFC18,  # 9: Pink
)

def check_exit(btn, hold_ms=500):
    """Check if BOOT button is held to return to menu."""
    if btn.value() == 0:
        t0 = time.ticks_ms()
        while btn.value() == 0:
            if time.ticks_diff(time.ticks_ms(), t0) >= hold_ms:
                while btn.value() == 0:
                    time.sleep_ms(10)
                time.sleep_ms(50)
                return True
            time.sleep_ms(10)
    return False

class Menu:
    def __init__(self, matrix, btn_pin=9, hold_ms=600):
        self.matrix = matrix
        self.btn = machine.Pin(btn_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.hold_ms = hold_ms
        self.apps = []
        self.current = 0

    def register(self, name, handler, color=None):
        idx = len(self.apps)
        c = color if color is not None else APP_COLORS[idx % len(APP_COLORS)]
        self.apps.append({"name": name, "handler": handler, "color": c})

    def draw_digit(self, num, color, x_off=1):
        rows = DIGITS[num % 10]
        for y, row in enumerate(rows):
            for x in range(3):
                if (row >> (2 - x)) & 1:
                    self.matrix.pixel(x_off + x, y, color)

    def draw_menu(self, dots=0):
        self.matrix.fill(0)
        if not self.apps:
            self.matrix.show()
            return
        app = self.apps[self.current]
        num = self.current + 1
        self.draw_digit(num, app["color"], x_off=1)
        # Hold progress bar on column 5 (bottom to top)
        for i in range(dots):
            self.matrix.pixel(5, 4 - i, 0xFFFF)
        self.matrix.show()

    def run(self):
        if not self.apps:
            return

        self.draw_menu()

        while True:
            if self.btn.value() == 0:
                t0 = time.ticks_ms()
                long_pressed = False
                prev_dots = 0

                while self.btn.value() == 0:
                    held = time.ticks_diff(time.ticks_ms(), t0)
                    dots = min(5, (held * 5) // self.hold_ms)
                    if dots != prev_dots:
                        prev_dots = dots
                        self.draw_menu(dots=dots)

                    if held >= self.hold_ms:
                        long_pressed = True
                        break
                    time.sleep_ms(20)

                if long_pressed:
                    # Flash confirmation
                    self.matrix.fill(0xFFFF)
                    self.matrix.show()
                    time.sleep_ms(60)
                    self.matrix.fill(0)
                    self.matrix.show()

                    # Wait for button release
                    while self.btn.value() == 0:
                        time.sleep_ms(10)
                    time.sleep_ms(50)

                    # Launch app
                    app = self.apps[self.current]
                    try:
                        app["handler"](self.matrix, self.btn)
                    except TypeError:
                        try:
                            app["handler"](self.matrix)
                        except TypeError:
                            app["handler"]()
                    except Exception as e:
                        print("App exception:", e)

                    # Return to menu
                    self.draw_menu()
                else:
                    # Short press: cycle to next app
                    if time.ticks_diff(time.ticks_ms(), t0) > 30:
                        self.current = (self.current + 1) % len(self.apps)
                        self.draw_menu()
                        while self.btn.value() == 0:
                            time.sleep_ms(10)
                        time.sleep_ms(50)

            time.sleep_ms(30)
