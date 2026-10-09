# apps/pong.py - App 5: Tilt-Steered Arcade Pong
import math

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
