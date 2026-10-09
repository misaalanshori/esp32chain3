# apps/dice.py - App 4: Shake-to-Roll Digital Dice
import urandom
from menu import DIGITS

async def app_dice(ctx):
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
