# apps.py - Built-in applications for 6x5 NeoMatrix
import machine
import time
import urandom
from state import system_state

MATRIX_WIDTH = const(6)
MATRIX_HEIGHT = const(5)

# --- Button Polling Helper ---
def poll_btn(btn, hold_ms=500):
    if system_state.requested_app is not None:
        return "exit"
    if btn.value() == 0:
        t0 = time.ticks_ms()
        while btn.value() == 0:
            if time.ticks_diff(time.ticks_ms(), t0) >= hold_ms:
                while btn.value() == 0:
                    time.sleep_ms(10)
                time.sleep_ms(50)
                return "exit"
            time.sleep_ms(10)
        time.sleep_ms(30)
        return "tap"
    return None

# --- IMU Shared Instance ---
_imu = None
def get_imu():
    global _imu
    if _imu is None:
        try:
            from MPU6050 import MPU6050
            pwr = machine.Pin(2, machine.Pin.OUT)
            pwr.value(1)
            time.sleep_ms(30)
            i2c = machine.SoftI2C(scl=machine.Pin(4), sda=machine.Pin(3))
            _imu = MPU6050(i2c=i2c)
        except Exception as e:
            print("IMU init failed:", e)
            return None
    return _imu

# --- Color Utilities ---
@micropython.native
def hsv_to_rgb(h, s, v):
    h = h % 360
    i = int(h * 0.016)
    f = (h * 0.016) - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    return int(r * 255), int(g * 255), int(b * 255)

def rgb_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# ==========================================
# App 1: Animated Rainbow Wave
# ==========================================
def app_rainbow(matrix, btn):
    offset = 0
    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        for x in range(MATRIX_WIDTH):
            for y in range(MATRIX_HEIGHT):
                h = ((x + y) * 36 + offset) % 360
                r, g, b = hsv_to_rgb(h, 0.9, 0.4)
                matrix.pixel(x, y, rgb_to_rgb565(r, g, b))
        matrix.show()
        offset = (offset + 12) % 360
        time.sleep_ms(25)

# ==========================================
# App 2: Jedag-Jedug (Fast Color Wheel)
# ==========================================
def app_jedagjedug(matrix, btn):
    np = matrix.neopixel
    num_pixels = len(np)
    j = 0
    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        for i in range(num_pixels):
            np[i] = wheel((i * 8 + j) & 255)
        np.write()
        j = (j + 4) & 255
        time.sleep_ms(20)

# ==========================================
# App 3: MPU6050 Bubble Level
# ==========================================
def app_bubble(matrix, btn):
    imu = get_imu()
    if not imu:
        return

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        try:
            acc = imu.read_accel_data()
            ax, ay, az = acc["x"], acc["y"], acc["z"]
            temp = imu.read_temperature()
            system_state.set_sensor(ax, ay, az, temp)

            bx = min(5, max(0, int(round(2.5 + (ax / 9.8) * 2.5))))
            by = min(4, max(0, int(round(2.0 + (ay / 9.8) * 2.0))))

            matrix.fill(0)
            # Center target crosshairs
            matrix.pixel(2, 2, 0x18C3)
            matrix.pixel(3, 2, 0x18C3)

            # Bubble color based on tilt deviation
            if (bx in (2, 3)) and by == 2:
                color = 0x07E0  # Green: level
            elif (bx in (1, 4)) or (by in (1, 3)):
                color = 0xFFE0  # Yellow: slight tilt
            else:
                color = 0xF800  # Red: steep tilt

            matrix.pixel(bx, by, color)
            matrix.show()
        except Exception:
            pass
        time.sleep_ms(40)

# ==========================================
# App 4: ShakeDice (Shake to Roll 1-6)
# ==========================================
def app_dice(matrix, btn):
    from menu import DIGITS
    imu = get_imu()

    def draw_num(num, color=0xFFE0):
        matrix.fill(0)
        rows = DIGITS[num % 10]
        for y, row in enumerate(rows):
            for x in range(3):
                if (row >> (2 - x)) & 1:
                    matrix.pixel(1 + x, y, color)
        matrix.show()

    current_val = (urandom.getrandbits(8) % 6) + 1
    draw_num(current_val)

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break

        shake = False
        if act == "tap":
            shake = True
        elif imu:
            try:
                acc = imu.read_accel_data()
                mag = abs(acc["x"]) + abs(acc["y"]) + abs(acc["z"])
                if mag > 19.0:  # Shake detected
                    shake = True
            except Exception:
                pass

        if shake:
            # Tumble animation
            for _ in range(8):
                draw_num((urandom.getrandbits(8) % 6) + 1, color=0xFD20)
                time.sleep_ms(50)
            current_val = (urandom.getrandbits(8) % 6) + 1
            draw_num(current_val, color=0x07E0)
            time.sleep_ms(300)

        time.sleep_ms(30)

# ==========================================
# App 5: TiltPong (IMU Paddle Arcade)
# ==========================================
def app_pong(matrix, btn):
    imu = get_imu()
    paddle_x = 2
    ball_x, ball_y = 2.0, 1.0
    vx, vy = 0.5, 0.4
    score = 0

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break

        # Move paddle by tilt
        if imu:
            try:
                acc = imu.read_accel_data()
                ax = acc["x"]
                paddle_x = min(4, max(0, int(round(2.0 + (ax / 6.0) * 2.0))))
            except Exception:
                pass

        # Move ball
        ball_x += vx
        ball_y += vy

        # Bounce walls
        if ball_x <= 0:
            ball_x = 0
            vx = abs(vx)
        elif ball_x >= 5:
            ball_x = 5
            vx = -abs(vx)

        if ball_y <= 0:
            ball_y = 0
            vy = abs(vy)
        elif ball_y >= 4:
            # Paddle collision check
            bx = int(round(ball_x))
            if paddle_x <= bx <= (paddle_x + 1):
                ball_y = 3
                vy = -abs(vy)
                score += 1
            else:
                # Missed: flash red and restart
                matrix.fill(0xF800)
                matrix.show()
                time.sleep_ms(200)
                ball_x, ball_y = 2.0, 1.0
                vx = 0.5 if (urandom.getrandbits(1)) else -0.5
                vy = 0.4
                score = 0

        # Draw frame
        matrix.fill(0)
        # Paddle: 2 cyan pixels on row 4
        matrix.pixel(paddle_x, 4, 0x07FF)
        matrix.pixel(paddle_x + 1, 4, 0x07FF)
        # Ball: bright white/yellow
        matrix.pixel(int(round(ball_x)), int(round(ball_y)), 0xFFFF)
        matrix.show()
        time.sleep_ms(40)

# ==========================================
# App 6: Hourglass (Physics Falling Sand)
# ==========================================
def app_hourglass(matrix, btn):
    imu = get_imu()
    # 8 sand grains: list of [x, y]
    grains = [
        [2, 0], [3, 0],
        [1, 1], [2, 1], [3, 1], [4, 1],
        [2, 2], [3, 2]
    ]
    colors = [0xFFE0, 0x07FF, 0xF81F]  # Gold, Cyan, Magenta
    c_idx = 0

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        if act == "tap":
            c_idx = (c_idx + 1) % len(colors)

        dx, dy = 0, 1  # default gravity down
        if imu:
            try:
                acc = imu.read_accel_data()
                ax, ay = acc["x"], acc["y"]
                if abs(ax) > abs(ay):
                    dx = 1 if ax > 2.0 else (-1 if ax < -2.0 else 0)
                    dy = 0
                else:
                    dy = 1 if ay > 2.0 else (-1 if ay < -2.0 else 0)
                    dx = 0
            except Exception:
                pass

        if dx != 0 or dy != 0:
            # Shift grains towards gravity
            occupied = set((gx, gy) for gx, gy in grains)
            for g in grains:
                nx = min(5, max(0, g[0] + dx))
                ny = min(4, max(0, g[1] + dy))
                if (nx, ny) not in occupied:
                    occupied.remove((g[0], g[1]))
                    g[0], g[1] = nx, ny
                    occupied.add((nx, ny))

        # Render
        matrix.fill(0)
        col = colors[c_idx]
        for gx, gy in grains:
            matrix.pixel(gx, gy, col)
        matrix.show()
        time.sleep_ms(70)

# ==========================================
# App 7: Conway's Game of Life
# ==========================================
def app_life(matrix, btn):
    w, h = MATRIX_WIDTH, MATRIX_HEIGHT
    grid = bytearray(w * h)

    def randomize():
        for i in range(len(grid)):
            grid[i] = 1 if (urandom.getrandbits(8) < 90) else 0

    randomize()
    stuck_count = 0

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        if act == "tap":
            randomize()

        new_grid = bytearray(w * h)
        alive = 0
        for y in range(h):
            for x in range(w):
                # Count neighbors (toroidal wrap)
                n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % w
                        ny = (y + dy) % h
                        if grid[ny * w + nx] > 0:
                            n += 1

                idx = y * w + x
                state = grid[idx]
                if state > 0:
                    if n == 2 or n == 3:
                        new_grid[idx] = min(4, state + 1)
                        alive += 1
                else:
                    if n == 3:
                        new_grid[idx] = 1
                        alive += 1

        # Check stagnation
        if alive == 0 or new_grid == grid:
            stuck_count += 1
            if stuck_count > 6:
                randomize()
                stuck_count = 0
        else:
            stuck_count = 0
            grid = new_grid

        # Render: Age colored
        matrix.fill(0)
        for y in range(h):
            for x in range(w):
                age = grid[y * w + x]
                if age == 1:
                    c = 0xFFFF  # New: White
                elif age == 2:
                    c = 0x07E0  # Youth: Green
                elif age == 3:
                    c = 0xFFE0  # Mid: Yellow
                elif age >= 4:
                    c = 0xF800  # Old: Red
                else:
                    c = 0
                if c != 0:
                    matrix.pixel(x, y, c)
        matrix.show()
        time.sleep_ms(140)

# ==========================================
# App 8: Retro Fire / Flame Simulation
# ==========================================
def app_fire(matrix, btn):
    w, h = MATRIX_WIDTH, MATRIX_HEIGHT
    heat = bytearray(w * (h + 1))  # Extra bottom row for embers
    palettes = [
        # 0: Campfire (Red/Amber/Yellow/White)
        (0x0000, 0x8000, 0xF800, 0xFD20, 0xFFE0, 0xFFFF),
        # 1: Blue Plasma
        (0x0000, 0x0010, 0x001F, 0x041F, 0x07FF, 0xFFFF),
        # 2: Toxic Green
        (0x0000, 0x0200, 0x0400, 0x07E0, 0x87E0, 0xFFFF),
    ]
    pal_idx = 0

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        if act == "tap":
            pal_idx = (pal_idx + 1) % len(palettes)

        # Generate bottom spark embers
        for x in range(w):
            heat[h * w + x] = 255 if (urandom.getrandbits(8) > 100) else 0

        # Diffuse upward
        for y in range(h):
            for x in range(w):
                src_y = y + 1
                left = (x - 1 + w) % w
                right = (x + 1) % w
                sum_heat = heat[src_y * w + x] + heat[src_y * w + left] + heat[src_y * w + right]
                avg = (sum_heat // 3)
                cool = urandom.getrandbits(4) + 6
                heat[y * w + x] = max(0, avg - cool)

        # Render
        pal = palettes[pal_idx]
        matrix.fill(0)
        for y in range(h):
            for x in range(w):
                val = heat[y * w + x]
                # Map 0-255 to 0-5
                c_step = min(5, val // 42)
                matrix.pixel(x, y, pal[c_step])
        matrix.show()
        time.sleep_ms(40)

# ==========================================
# App 9: ReflexGame (Reaction Speed Tester)
# ==========================================
def app_reflex(matrix, btn):
    while True:
        # 1. Ready state: 1 blue dot
        matrix.fill(0)
        matrix.pixel(2, 2, 0x001F)
        matrix.pixel(3, 2, 0x001F)
        matrix.show()

        # Random wait: 1.5 to 4.0 seconds
        wait_ms = 1500 + (urandom.getrandbits(12) % 2500)
        t_start = time.ticks_ms()
        false_start = False

        while time.ticks_diff(time.ticks_ms(), t_start) < wait_ms:
            act = poll_btn(btn)
            if act == "exit":
                return
            if act == "tap":
                false_start = True
                break
            time.sleep_ms(20)

        if false_start:
            # Flash RED for early press
            matrix.fill(0xF800)
            matrix.show()
            time.sleep_ms(500)
            continue

        # 2. TRIGGER: Full GREEN screen
        matrix.fill(0x07E0)
        matrix.show()
        t_green = time.ticks_ms()

        # Measure response time
        reacted = False
        reaction_ms = 0
        while time.ticks_diff(time.ticks_ms(), t_green) < 2000:
            if btn.value() == 0:
                reaction_ms = time.ticks_diff(time.ticks_ms(), t_green)
                reacted = True
                while btn.value() == 0:
                    time.sleep_ms(10)
                break
            time.sleep_ms(5)

        # 3. Display Score (Rating 1 to 5 dots on column 5)
        matrix.fill(0)
        if reacted:
            # Score dots based on reaction time
            if reaction_ms < 220:
                dots = 5
                col = 0x07E0  # Green
            elif reaction_ms < 280:
                dots = 4
                col = 0x07E0
            elif reaction_ms < 350:
                dots = 3
                col = 0xFFE0  # Yellow
            elif reaction_ms < 450:
                dots = 2
                col = 0xFD20  # Orange
            else:
                dots = 1
                col = 0xF800  # Red

            for d in range(dots):
                matrix.pixel(5, 4 - d, col)

            # Draw a thumbs up / smiley or level indicator
            matrix.pixel(1, 2, col)
            matrix.pixel(2, 2, col)
            matrix.pixel(3, 2, col)
            matrix.show()

            # Wait for tap to play again or hold to exit
            while True:
                act = poll_btn(btn)
                if act == "exit":
                    return
                if act == "tap":
                    break
                time.sleep_ms(30)
        else:
            # Timed out
            time.sleep_ms(500)

# Helper to parse hex color
def parse_hex_color(hex_str):
    try:
        s = hex_str.lstrip('#')
        if len(s) == 6:
            return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except Exception:
        pass
    return 255, 255, 255

# ==========================================
# App 10: WebPaint (Canvas & Frame Animator)
# ==========================================
def app_paint(matrix, btn):
    frame_idx = 0
    last_frame_time = time.ticks_ms()

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        if act == "tap":
            if len(system_state.paint_frames) > 1:
                frame_idx = (frame_idx + 1) % len(system_state.paint_frames)
            else:
                system_state.paint_frames = [["#000000"] * 30]

        frames = system_state.paint_frames
        speed = max(40, system_state.paint_speed)

        if len(frames) > 1:
            if time.ticks_diff(time.ticks_ms(), last_frame_time) >= speed:
                frame_idx = (frame_idx + 1) % len(frames)
                last_frame_time = time.ticks_ms()
        else:
            frame_idx = 0

        current_frame = frames[frame_idx % len(frames)]
        matrix.fill(0)
        for i, c in enumerate(current_frame):
            if i < 30 and c != "#000000":
                r, g, b = parse_hex_color(c)
                matrix.pixel(i % 6, i // 6, rgb_to_rgb565(r, g, b))
        matrix.show()
        time.sleep_ms(30)

# ==========================================
# App 11: WebTicker (Marquee Text Scroller)
# ==========================================
FONT_3x5 = {
    'A': (0b010, 0b101, 0b111, 0b101, 0b101),
    'B': (0b110, 0b101, 0b110, 0b101, 0b110),
    'C': (0b011, 0b100, 0b100, 0b100, 0b011),
    'D': (0b110, 0b101, 0b101, 0b101, 0b110),
    'E': (0b111, 0b100, 0b110, 0b100, 0b111),
    'F': (0b111, 0b100, 0b110, 0b100, 0b100),
    'G': (0b011, 0b100, 0b101, 0b101, 0b011),
    'H': (0b101, 0b101, 0b111, 0b101, 0b101),
    'I': (0b111, 0b010, 0b010, 0b010, 0b111),
    'J': (0b001, 0b001, 0b001, 0b101, 0b010),
    'K': (0b101, 0b110, 0b100, 0b110, 0b101),
    'L': (0b100, 0b100, 0b100, 0b100, 0b111),
    'M': (0b101, 0b111, 0b101, 0b101, 0b101),
    'N': (0b101, 0b111, 0b111, 0b101, 0b101),
    'O': (0b010, 0b101, 0b101, 0b101, 0b010),
    'P': (0b110, 0b101, 0b110, 0b100, 0b100),
    'Q': (0b010, 0b101, 0b101, 0b110, 0b011),
    'R': (0b110, 0b101, 0b110, 0b101, 0b101),
    'S': (0b011, 0b100, 0b010, 0b001, 0b110),
    'T': (0b111, 0b010, 0b010, 0b010, 0b010),
    'U': (0b101, 0b101, 0b101, 0b101, 0b010),
    'V': (0b101, 0b101, 0b101, 0b101, 0b010),
    'W': (0b101, 0b101, 0b101, 0b111, 0b101),
    'X': (0b101, 0b101, 0b010, 0b101, 0b101),
    'Y': (0b101, 0b101, 0b010, 0b010, 0b010),
    'Z': (0b111, 0b001, 0b010, 0b100, 0b111),
    '0': (0b111, 0b101, 0b101, 0b101, 0b111),
    '1': (0b010, 0b110, 0b010, 0b010, 0b111),
    '2': (0b111, 0b001, 0b111, 0b100, 0b111),
    '3': (0b111, 0b001, 0b111, 0b001, 0b111),
    '4': (0b101, 0b101, 0b111, 0b001, 0b001),
    '5': (0b111, 0b100, 0b111, 0b001, 0b111),
    '6': (0b111, 0b100, 0b111, 0b101, 0b111),
    '7': (0b111, 0b001, 0b001, 0b001, 0b001),
    '8': (0b111, 0b101, 0b111, 0b101, 0b111),
    '9': (0b111, 0b101, 0b111, 0b001, 0b111),
    ' ': (0b000, 0b000, 0b000, 0b000, 0b000),
    '!': (0b010, 0b010, 0b010, 0b000, 0b010),
    '?': (0b110, 0b001, 0b010, 0b000, 0b010),
    '-': (0b000, 0b000, 0b111, 0b000, 0b000),
    ':': (0b000, 0b010, 0b000, 0b010, 0b000),
    '.': (0b000, 0b000, 0b000, 0b000, 0b010),
}

def app_ticker(matrix, btn):
    paused = False
    last_text = ""
    col_bits = []

    def rebuild(txt):
        nonlocal col_bits, last_text
        last_text = txt
        col_bits = [[] for _ in range(5)]
        for y in range(5):
            col_bits[y].extend([0] * 6)
        for ch in txt.upper():
            glyph = FONT_3x5.get(ch, FONT_3x5.get(' ', (0,0,0,0,0)))
            for y in range(5):
                r = glyph[y]
                col_bits[y].extend([(r >> 2) & 1, (r >> 1) & 1, r & 1, 0])
        for y in range(5):
            col_bits[y].extend([0] * 6)

    rebuild(system_state.ticker_text)
    col_idx = 0

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        if act == "tap":
            paused = not paused

        if system_state.ticker_text != last_text:
            rebuild(system_state.ticker_text)
            col_idx = 0

        r, g, b = parse_hex_color(system_state.ticker_color)
        c565 = rgb_to_rgb565(r, g, b)

        matrix.fill(0)
        total_cols = len(col_bits[0])
        if total_cols > 6:
            for x in range(6):
                src_x = (col_idx + x) % total_cols
                for y in range(5):
                    if col_bits[y][src_x]:
                        matrix.pixel(x, y, c565)
        matrix.show()

        if not paused and total_cols > 6:
            col_idx = (col_idx + 1) % total_cols

        time.sleep_ms(max(30, system_state.ticker_speed))

# ==========================================
# App 12: WebStudio (Mood Lamp & Pattern Studio)
# ==========================================
def app_studio(matrix, btn):
    effects = ["candle", "breath", "strobe", "wave", "solid"]
    step = 0

    while True:
        act = poll_btn(btn)
        if act == "exit":
            break
        if act == "tap":
            curr_i = effects.index(system_state.studio_effect) if system_state.studio_effect in effects else 0
            system_state.studio_effect = effects[(curr_i + 1) % len(effects)]

        eff = system_state.studio_effect
        r0, g0, b0 = parse_hex_color(system_state.studio_color)
        speed = max(20, system_state.studio_speed)

        matrix.fill(0)
        if eff == "solid":
            c = rgb_to_rgb565(r0, g0, b0)
            matrix.fill(c)
        elif eff == "candle":
            for x in range(6):
                for y in range(5):
                    flick = urandom.getrandbits(5)
                    rf = max(0, min(255, r0 - flick))
                    gf = max(0, min(255, g0 - flick * 2))
                    bf = max(0, min(255, b0 - flick * 3))
                    matrix.pixel(x, y, rgb_to_rgb565(rf, gf, bf))
        elif eff == "breath":
            phase = (step % 40)
            factor = (phase / 20.0) if phase < 20 else (2.0 - phase / 20.0)
            factor = max(0.1, min(1.0, factor))
            c = rgb_to_rgb565(int(r0 * factor), int(g0 * factor), int(b0 * factor))
            matrix.fill(c)
        elif eff == "strobe":
            if (step % 2) == 0:
                for x in range(3):
                    for y in range(5):
                        matrix.pixel(x, y, 0xF800)
            else:
                for x in range(3, 6):
                    for y in range(5):
                        matrix.pixel(x, y, 0x001F)
        elif eff == "wave":
            for x in range(6):
                col_factor = ((x + step) % 6) / 5.0
                c = rgb_to_rgb565(int(r0 * col_factor), int(g0 * col_factor), int(b0 * col_factor))
                for y in range(5):
                    matrix.pixel(x, y, c)

        matrix.show()
        step += 1
        time.sleep_ms(speed)

# ==========================================
# Full 12 Registered Apps
# ==========================================
REGISTERED_APPS = (
    ("Rainbow", app_rainbow),
    ("JedagJedug", app_jedagjedug),
    ("BubbleLevel", app_bubble),
    ("ShakeDice", app_dice),
    ("TiltPong", app_pong),
    ("Hourglass", app_hourglass),
    ("GameOfLife", app_life),
    ("FireSim", app_fire),
    ("ReflexGame", app_reflex),
    ("WebPaint", app_paint),
    ("WebTicker", app_ticker),
    ("WebStudio", app_studio),
)
