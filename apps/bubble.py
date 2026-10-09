# apps/bubble.py - App 3: MPU6050 Accelerometer Bubble Level
import math

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
