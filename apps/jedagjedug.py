# apps/jedagjedug.py - App 2: Fast Color Strobe / Rainbow Wheel
from apps.utils import wheel

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
