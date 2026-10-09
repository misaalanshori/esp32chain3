# apps/rainbow.py - App 1: Animated Rainbow Wave
from apps.utils import MATRIX_WIDTH, MATRIX_HEIGHT, hsv_to_rgb, rgb_to_rgb565

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
