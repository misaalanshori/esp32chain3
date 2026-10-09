# apps/reflex.py - App 9: Millisecond Reaction Speed Tester
import time
import urandom

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
