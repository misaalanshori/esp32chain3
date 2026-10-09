# apps/paint.py - App 10: Web Canvas & Flipbook Animation Player
import time
from apps.utils import parse_hex_color, rgb_to_rgb565

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
