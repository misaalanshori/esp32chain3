# apps/hourglass.py - App 6: Gravity Particle Falling Sand
async def app_hourglass(ctx):
    imu = ctx.get_imu()
    grains = [[2,0],[3,0],[1,1],[2,1],[3,1],[4,1],[2,2],[3,2]]
    colors = [0xFFE0, 0x07FF, 0xF81F]
    c_idx = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap": c_idx = (c_idx + 1) % len(colors)
        dx, dy = 0, 1
        if imu:
            try:
                acc = imu.read_accel_data()
                ax, ay = acc["x"], acc["y"]
                if abs(ax) > abs(ay): dx = 1 if ax > 2.0 else (-1 if ax < -2.0 else 0); dy = 0
                else: dy = 1 if ay > 2.0 else (-1 if ay < -2.0 else 0); dx = 0
            except Exception: pass
        if dx != 0 or dy != 0:
            occ = set((gx, gy) for gx, gy in grains)
            for g in grains:
                nx, ny = min(5, max(0, g[0] + dx)), min(4, max(0, g[1] + dy))
                if (nx, ny) not in occ:
                    occ.remove((g[0], g[1]))
                    g[0], g[1] = nx, ny
                    occ.add((nx, ny))
        ctx.matrix.fill(0)
        col = colors[c_idx]
        for gx, gy in grains: ctx.matrix.pixel(gx, gy, col)
        ctx.matrix.show()
        await ctx.sleep_ms(70)
