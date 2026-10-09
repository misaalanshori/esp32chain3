# apps/life.py - App 7: Conway's Game of Life Cellular Automata
import urandom
from apps.utils import MATRIX_WIDTH, MATRIX_HEIGHT

async def app_life(ctx):
    w, h = MATRIX_WIDTH, MATRIX_HEIGHT
    grid = bytearray(w * h)
    def randomize():
        for i in range(len(grid)): grid[i] = 1 if (urandom.getrandbits(8) < 90) else 0
    randomize()
    stuck = 0
    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit": break
        if act == "tap": randomize()
        new_grid = bytearray(w * h)
        alive = 0
        for y in range(h):
            for x in range(w):
                n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0: continue
                        if grid[((y + dy) % h) * w + ((x + dx) % w)] > 0: n += 1
                idx = y * w + x
                st = grid[idx]
                if st > 0:
                    if n == 2 or n == 3: new_grid[idx] = min(4, st + 1); alive += 1
                elif n == 3: new_grid[idx] = 1; alive += 1
        if alive == 0 or new_grid == grid:
            stuck += 1
            if stuck > 6: randomize(); stuck = 0
        else:
            stuck = 0; grid = new_grid
        ctx.matrix.fill(0)
        for y in range(h):
            for x in range(w):
                age = grid[y * w + x]
                if age:
                    c = 0xFFFF if age == 1 else (0x07E0 if age == 2 else (0xFFE0 if age == 3 else 0xF800))
                    ctx.matrix.pixel(x, y, c)
        ctx.matrix.show()
        await ctx.sleep_ms(140)
