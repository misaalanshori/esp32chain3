# apps/studio.py - App 12: Procedural Ambient Lighting Studio
import urandom
from apps.utils import parse_hex_color, rgb_to_rgb565

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
