# apps.py - Preemptible, Non-Blocking Async Micro-Applications
import time
import urandom

MATRIX_WIDTH = const(6)
MATRIX_HEIGHT = const(5)

def rgb_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def parse_hex_color(hex_str):
    try:
        s = hex_str.lstrip('#')
        if len(s) == 6:
            return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except Exception:
        pass
    return 255, 255, 255

@micropython.native
def hsv_to_rgb(h, s, v):
    h = h % 360
    i = int(h * 0.016)
    f = (h * 0.016) - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)

def wheel(pos):
    if pos < 85: return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# App 1: Rainbow
async def app_rainbow(ctx):
    offset = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        for x in range(MATRIX_WIDTH):
            for y in range(MATRIX_HEIGHT):
                h = ((x + y) * 36 + offset) % 360
                r, g, b = hsv_to_rgb(h, 0.9, 0.4)
                ctx.matrix.pixel(x, y, rgb_to_rgb565(r, g, b))
        ctx.matrix.show()
        offset = (offset + 12) % 360
        await ctx.sleep_ms(25)

# App 2: JedagJedug
async def app_jedagjedug(ctx):
    np = ctx.matrix.neopixel
    num_pixels = len(np)
    j = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        for i in range(num_pixels):
            np[i] = wheel((i * 8 + j) & 255)
        np.write()
        j = (j + 4) & 255
        await ctx.sleep_ms(20)

# App 3: BubbleLevel
async def app_bubble(ctx):
    imu = ctx.get_imu()
    if not imu: return
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        try:
            acc = imu.read_accel_data()
            ax, ay, az = acc["x"], acc["y"], acc["z"]
            temp = imu.read_temperature()
            ctx.state.set_sensor(ax, ay, az, temp)
            bx = min(5, max(0, int(round(2.5 + (ax / 9.8) * 2.5))))
            by = min(4, max(0, int(round(2.0 + (ay / 9.8) * 2.0))))
            ctx.matrix.fill(0)
            ctx.matrix.pixel(2, 2, 0x18C3)
            ctx.matrix.pixel(3, 2, 0x18C3)
            color = 0x07E0 if (bx in (2, 3) and by == 2) else (0xFFE0 if (bx in (1, 4) or by in (1, 3)) else 0xF800)
            ctx.matrix.pixel(bx, by, color)
            ctx.matrix.show()
        except Exception:
            pass
        await ctx.sleep_ms(40)

# App 4: ShakeDice
async def app_dice(ctx):
    from menu import DIGITS
    imu = ctx.get_imu()
    def draw_num(num, col=0xFFE0):
        ctx.matrix.fill(0)
        rows = DIGITS[num % 10]
        for y, row in enumerate(rows):
            for x in range(3):
                if (row >> (2 - x)) & 1: ctx.matrix.pixel(1 + x, y, col)
        ctx.matrix.show()

    val = (urandom.getrandbits(8) % 6) + 1
    draw_num(val)
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        shake = (act == "tap")
        if not shake and imu:
            try:
                acc = imu.read_accel_data()
                if (abs(acc["x"]) + abs(acc["y"]) + abs(acc["z"])) > 19.0: shake = True
            except Exception: pass
        if shake:
            for _ in range(8):
                draw_num((urandom.getrandbits(8) % 6) + 1, col=0xFD20)
                await ctx.sleep_ms(50)
            val = (urandom.getrandbits(8) % 6) + 1
            draw_num(val, col=0x07E0)
            await ctx.sleep_ms(250)
        await ctx.sleep_ms(30)

# App 5: TiltPong
async def app_pong(ctx):
    imu = ctx.get_imu()
    paddle_x = 2
    ball_x, ball_y = 2.0, 1.0
    vx, vy = 0.5, 0.4
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if imu:
            try:
                acc = imu.read_accel_data()
                paddle_x = min(4, max(0, int(round(2.0 + (acc["x"] / 6.0) * 2.0))))
            except Exception: pass
        ball_x += vx
        ball_y += vy
        if ball_x <= 0: ball_x = 0; vx = abs(vx)
        elif ball_x >= 5: ball_x = 5; vx = -abs(vx)
        if ball_y <= 0: ball_y = 0; vy = abs(vy)
        elif ball_y >= 4:
            bx = int(round(ball_x))
            if paddle_x <= bx <= (paddle_x + 1):
                ball_y = 3; vy = -abs(vy)
            else:
                ctx.matrix.fill(0xF800)
                ctx.matrix.show()
                await ctx.sleep_ms(200)
                ball_x, ball_y = 2.0, 1.0
                vx, vy = 0.5, 0.4
        ctx.matrix.fill(0)
        ctx.matrix.pixel(paddle_x, 4, 0x07FF)
        ctx.matrix.pixel(paddle_x + 1, 4, 0x07FF)
        ctx.matrix.pixel(int(round(ball_x)), int(round(ball_y)), 0xFFFF)
        ctx.matrix.show()
        await ctx.sleep_ms(40)

# App 6: Hourglass
async def app_hourglass(ctx):
    imu = ctx.get_imu()
    grains = [[2,0],[3,0],[1,1],[2,1],[3,1],[4,1],[2,2],[3,2]]
    colors = [0xFFE0, 0x07FF, 0xF81F]
    c_idx = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap": c_idx = (c_idx + 1) % len(colors)
        dx, dy = 0, 1
        if imu:
            try:
                acc = imu.read_accel_data()
                ax, ay = acc["x"], acc["y"]
                if abs(ax) > abs(ay): dx = 1 if ax > 2.0 else (-1 if ax < -2.0 else 0); dy = 0
                else: dy = 1 if ay > 2.0 else (-1 if ay < -2.0 else 0); dx = 0
            except Exception: pass
        if dx != 0 or dy != 0:
            occ = set((gx, gy) for gx, gy in grains)
            for g in grains:
                nx, ny = min(5, max(0, g[0] + dx)), min(4, max(0, g[1] + dy))
                if (nx, ny) not in occ:
                    occ.remove((g[0], g[1]))
                    g[0], g[1] = nx, ny
                    occ.add((nx, ny))
        ctx.matrix.fill(0)
        col = colors[c_idx]
        for gx, gy in grains: ctx.matrix.pixel(gx, gy, col)
        ctx.matrix.show()
        await ctx.sleep_ms(70)

# App 7: GameOfLife
async def app_life(ctx):
    w, h = MATRIX_WIDTH, MATRIX_HEIGHT
    grid = bytearray(w * h)
    def randomize():
        for i in range(len(grid)): grid[i] = 1 if (urandom.getrandbits(8) < 90) else 0
    randomize()
    stuck = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap": randomize()
        new_grid = bytearray(w * h)
        alive = 0
        for y in range(h):
            for x in range(w):
                n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0: continue
                        if grid[((y + dy) % h) * w + ((x + dx) % w)] > 0: n += 1
                idx = y * w + x
                st = grid[idx]
                if st > 0:
                    if n == 2 or n == 3: new_grid[idx] = min(4, st + 1); alive += 1
                elif n == 3: new_grid[idx] = 1; alive += 1
        if alive == 0 or new_grid == grid:
            stuck += 1
            if stuck > 6: randomize(); stuck = 0
        else:
            stuck = 0; grid = new_grid
        ctx.matrix.fill(0)
        for y in range(h):
            for x in range(w):
                age = grid[y * w + x]
                if age:
                    c = 0xFFFF if age == 1 else (0x07E0 if age == 2 else (0xFFE0 if age == 3 else 0xF800))
                    ctx.matrix.pixel(x, y, c)
        ctx.matrix.show()
        await ctx.sleep_ms(140)

# App 8: FireSim
async def app_fire(ctx):
    w, h = MATRIX_WIDTH, MATRIX_HEIGHT
    heat = bytearray(w * (h + 1))
    palettes = [
        (0x0000, 0x8000, 0xF800, 0xFD20, 0xFFE0, 0xFFFF),
        (0x0000, 0x0010, 0x001F, 0x041F, 0x07FF, 0xFFFF),
        (0x0000, 0x0200, 0x0400, 0x07E0, 0x87E0, 0xFFFF),
    ]
    pal_idx = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap": pal_idx = (pal_idx + 1) % len(palettes)
        for x in range(w): heat[h * w + x] = 255 if (urandom.getrandbits(8) > 100) else 0
        for y in range(h):
            for x in range(w):
                src = (y + 1) * w
                avg = (heat[src + x] + heat[src + ((x - 1 + w) % w)] + heat[src + ((x + 1) % w)]) // 3
                heat[y * w + x] = max(0, avg - (urandom.getrandbits(4) + 6))
        ctx.matrix.fill(0)
        pal = palettes[pal_idx]
        for y in range(h):
            for x in range(w):
                ctx.matrix.pixel(x, y, pal[min(5, heat[y * w + x] // 42)])
        ctx.matrix.show()
        await ctx.sleep_ms(40)

# App 9: ReflexGame
async def app_reflex(ctx):
    while not ctx.should_stop():
        ctx.matrix.fill(0)
        ctx.matrix.pixel(2, 2, 0x001F); ctx.matrix.pixel(3, 2, 0x001F)
        ctx.matrix.show()
        wait_ms = 1500 + (urandom.getrandbits(12) % 2500)
        t_start = time.ticks_ms()
        false_start = False
        while time.ticks_diff(time.ticks_ms(), t_start) < wait_ms:
            act = ctx.poll_action(ctx.app_manager.button)
            if act == "exit": return
            if act == "tap": false_start = True; break
            await ctx.sleep_ms(20)
        if false_start:
            ctx.matrix.fill(0xF800); ctx.matrix.show()
            await ctx.sleep_ms(500); continue

        ctx.matrix.fill(0x07E0); ctx.matrix.show()
        t_green = time.ticks_ms()
        reacted = False
        while time.ticks_diff(time.ticks_ms(), t_green) < 2000:
            if ctx.app_manager.button.value() == 0:
                dt = time.ticks_diff(time.ticks_ms(), t_green)
                reacted = True
                while ctx.app_manager.button.value() == 0: await ctx.sleep_ms(10)
                break
            await ctx.sleep_ms(5)

        ctx.matrix.fill(0)
        if reacted:
            dots = 5 if dt < 220 else (4 if dt < 280 else (3 if dt < 350 else (2 if dt < 450 else 1)))
            col = 0x07E0 if dots >= 4 else (0xFFE0 if dots == 3 else 0xF800)
            for d in range(dots): ctx.matrix.pixel(5, 4 - d, col)
            ctx.matrix.pixel(1, 2, col); ctx.matrix.pixel(2, 2, col); ctx.matrix.pixel(3, 2, col)
            ctx.matrix.show()
            while not ctx.should_stop():
                act = ctx.poll_action(ctx.app_manager.button)
                if act == "exit": return
                if act == "tap": break
                await ctx.sleep_ms(30)
        else:
            await ctx.sleep_ms(500)

# App 10: WebPaint
async def app_paint(ctx):
    frame_idx = 0
    last_frame = time.ticks_ms()
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap":
            if len(ctx.state.paint_frames) > 1: frame_idx = (frame_idx + 1) % len(ctx.state.paint_frames)
            else: ctx.state.paint_frames = [["#000000"] * 30]
        frames = ctx.state.paint_frames
        speed = max(40, ctx.state.paint_speed)
        if len(frames) > 1 and time.ticks_diff(time.ticks_ms(), last_frame) >= speed:
            frame_idx = (frame_idx + 1) % len(frames)
            last_frame = time.ticks_ms()
        current = frames[frame_idx % len(frames)]
        ctx.matrix.fill(0)
        for i, c in enumerate(current):
            if i < 30 and c != "#000000":
                r, g, b = parse_hex_color(c)
                ctx.matrix.pixel(i % 6, i // 6, rgb_to_rgb565(r, g, b))
        ctx.matrix.show()
        await ctx.sleep_ms(30)

# App 11: WebTicker
FONT_3x5 = {
    'A': (0b010, 0b101, 0b111, 0b101, 0b101), 'B': (0b110, 0b101, 0b110, 0b101, 0b110),
    'C': (0b011, 0b100, 0b100, 0b100, 0b011), 'D': (0b110, 0b101, 0b101, 0b101, 0b110),
    'E': (0b111, 0b100, 0b110, 0b100, 0b111), 'F': (0b111, 0b100, 0b110, 0b100, 0b100),
    'G': (0b011, 0b100, 0b101, 0b101, 0b011), 'H': (0b101, 0b101, 0b111, 0b101, 0b101),
    'I': (0b111, 0b010, 0b010, 0b010, 0b111), 'J': (0b001, 0b001, 0b001, 0b101, 0b010),
    'K': (0b101, 0b110, 0b100, 0b110, 0b101), 'L': (0b100, 0b100, 0b100, 0b100, 0b111),
    'M': (0b101, 0b111, 0b101, 0b101, 0b101), 'N': (0b101, 0b111, 0b111, 0b101, 0b101),
    'O': (0b010, 0b101, 0b101, 0b101, 0b010), 'P': (0b110, 0b101, 0b110, 0b100, 0b100),
    'Q': (0b010, 0b101, 0b101, 0b110, 0b011), 'R': (0b110, 0b101, 0b110, 0b101, 0b101),
    'S': (0b011, 0b100, 0b010, 0b001, 0b110), 'T': (0b111, 0b010, 0b010, 0b010, 0b010),
    'U': (0b101, 0b101, 0b101, 0b101, 0b010), 'V': (0b101, 0b101, 0b101, 0b101, 0b010),
    'W': (0b101, 0b101, 0b101, 0b111, 0b101), 'X': (0b101, 0b101, 0b010, 0b101, 0b101),
    'Y': (0b101, 0b101, 0b010, 0b010, 0b010), 'Z': (0b111, 0b001, 0b010, 0b100, 0b111),
    '0': (0b111, 0b101, 0b101, 0b101, 0b111), '1': (0b010, 0b110, 0b010, 0b010, 0b111),
    '2': (0b111, 0b001, 0b111, 0b100, 0b111), '3': (0b111, 0b001, 0b111, 0b001, 0b111),
    '4': (0b101, 0b101, 0b111, 0b001, 0b001), '5': (0b111, 0b100, 0b111, 0b001, 0b111),
    '6': (0b111, 0b100, 0b111, 0b101, 0b111), '7': (0b111, 0b001, 0b001, 0b001, 0b001),
    '8': (0b111, 0b101, 0b111, 0b101, 0b111), '9': (0b111, 0b101, 0b111, 0b001, 0b111),
    ' ': (0b000, 0b000, 0b000, 0b000, 0b000), '!': (0b010, 0b010, 0b010, 0b000, 0b010),
    '?': (0b110, 0b001, 0b010, 0b000, 0b010), '-': (0b000, 0b000, 0b111, 0b000, 0b000),
    ':': (0b000, 0b010, 0b000, 0b010, 0b000), '.': (0b000, 0b000, 0b000, 0b000, 0b010),
}

async def app_ticker(ctx):
    paused = False
    last_text = ""
    col_bits = []
    def rebuild(txt):
        nonlocal col_bits, last_text
        last_text = txt
        col_bits = [[] for _ in range(5)]
        for y in range(5): col_bits[y].extend([0] * 6)
        for ch in txt.upper():
            glyph = FONT_3x5.get(ch, FONT_3x5.get(' ', (0,0,0,0,0)))
            for y in range(5):
                r = glyph[y]
                col_bits[y].extend([(r >> 2) & 1, (r >> 1) & 1, r & 1, 0])
        for y in range(5): col_bits[y].extend([0] * 6)

    rebuild(ctx.state.ticker_text)
    col_idx = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap": paused = not paused
        if ctx.state.ticker_text != last_text:
            rebuild(ctx.state.ticker_text)
            col_idx = 0
        r, g, b = parse_hex_color(ctx.state.ticker_color)
        c565 = rgb_to_rgb565(r, g, b)
        ctx.matrix.fill(0)
        tot = len(col_bits[0])
        if tot > 6:
            for x in range(6):
                src_x = (col_idx + x) % tot
                for y in range(5):
                    if col_bits[y][src_x]: ctx.matrix.pixel(x, y, c565)
        ctx.matrix.show()
        if not paused and tot > 6: col_idx = (col_idx + 1) % tot
        await ctx.sleep_ms(max(30, ctx.state.ticker_speed))

# App 12: WebStudio
async def app_studio(ctx):
    effects = ["candle", "breath", "strobe", "wave", "solid"]
    step = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap":
            curr_i = effects.index(ctx.state.studio_effect) if ctx.state.studio_effect in effects else 0
            ctx.state.studio_effect = effects[(curr_i + 1) % len(effects)]
        eff = ctx.state.studio_effect
        r0, g0, b0 = parse_hex_color(ctx.state.studio_color)
        ctx.matrix.fill(0)
        if eff == "solid":
            ctx.matrix.fill(rgb_to_rgb565(r0, g0, b0))
        elif eff == "candle":
            for x in range(6):
                for y in range(5):
                    flick = urandom.getrandbits(5)
                    rf = max(0, min(255, r0 - flick))
                    gf = max(0, min(255, g0 - flick * 2))
                    bf = max(0, min(255, b0 - flick * 3))
                    ctx.matrix.pixel(x, y, rgb_to_rgb565(rf, gf, bf))
        elif eff == "breath":
            ph = (step % 40)
            fac = max(0.1, min(1.0, (ph / 20.0) if ph < 20 else (2.0 - ph / 20.0)))
            ctx.matrix.fill(rgb_to_rgb565(int(r0 * fac), int(g0 * fac), int(b0 * fac)))
        elif eff == "strobe":
            if (step % 2) == 0:
                for x in range(3):
                    for y in range(5): ctx.matrix.pixel(x, y, 0xF800)
            else:
                for x in range(3, 6):
                    for y in range(5): ctx.matrix.pixel(x, y, 0x001F)
        elif eff == "wave":
            for x in range(6):
                fac = ((x + step) % 6) / 5.0
                c = rgb_to_rgb565(int(r0 * fac), int(g0 * fac), int(b0 * fac))
                for y in range(5): ctx.matrix.pixel(x, y, c)
        ctx.matrix.show()
        step += 1
        await ctx.sleep_ms(max(20, ctx.state.studio_speed))

# App 13: MPU_FFT (High-Speed 3-Axis FFT & Energy Waterfall)
async def app_fft(ctx):
    import array
    from fft import FastFFT32

    imu = ctx.get_imu()
    if not imu:
        return

    fft_engine = FastFFT32()
    raw_buf = bytearray(6)
    x_samps = array.array('i', [0] * 32)
    y_samps = array.array('i', [0] * 32)
    z_samps = array.array('i', [0] * 32)
    history = [0, 0, 0, 0, 0, 0]
    BAR_COLORS = (0xF800, 0xFD20, 0xFFE0, 0x07EA, 0x07E0)

    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit":
            break
        if act == "tap":
            history = [0, 0, 0, 0, 0, 0]

        # Fast 3ms sampling (~300 Hz sample rate, < 5ms interval)
        for s in range(32):
            if ctx.should_stop():
                return
            try:
                ctx.imu_service.read_raw_accel_into(raw_buf)
                x = (raw_buf[0] << 8) | raw_buf[1]
                if x >= 32768: x -= 65536
                y = (raw_buf[2] << 8) | raw_buf[3]
                if y >= 32768: y -= 65536
                z = (raw_buf[4] << 8) | raw_buf[5]
                if z >= 32768: z -= 65536

                x_samps[s] = x
                y_samps[s] = y
                z_samps[s] = z
            except Exception:
                pass
            await ctx.sleep_ms(3)

        # 3-Axis FFT with DC offset removal and Hanning window
        mag_x, mag_y, mag_z, total_e = fft_engine.process_3axis(x_samps, y_samps, z_samps)
        ctx.state.set_fft_data(total_e, mag_x, mag_y, mag_z)

        # Dynamic movement energy mapped to bar height 0..5
        if total_e < 1200: h = 0
        elif total_e < 3500: h = 1
        elif total_e < 8000: h = 2
        elif total_e < 16000: h = 3
        elif total_e < 30000: h = 4
        else: h = 5

        for c in range(5):
            history[c] = history[c + 1]
        history[5] = h

        ctx.matrix.fill(0)
        for col in range(6):
            height = history[col]
            for row in range(height):
                ctx.matrix.pixel(col, 4 - row, BAR_COLORS[4 - row])
        ctx.matrix.show()

# Catalog of All 13 Apps
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
    ("MPU_FFT", app_fft),
)
