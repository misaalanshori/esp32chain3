# apps/fire.py - App 8: Retro Flame / Ember Diffusion Simulation
import urandom
from apps.utils import MATRIX_WIDTH, MATRIX_HEIGHT

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
