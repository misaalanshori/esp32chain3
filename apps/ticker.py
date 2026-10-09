# apps/ticker.py - App 11: Live Web Marquee Text Scroller
from apps.utils import FONT_3x5, parse_hex_color, rgb_to_rgb565

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
