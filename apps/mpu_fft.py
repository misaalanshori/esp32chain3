# apps/mpu_fft.py - App 13: Configurable High-Speed 3-Axis FFT & Energy Waterfall
import array
from fft import FastFFT

async def app_fft(ctx):
    imu = ctx.get_imu()
    if not imu:
        return

    fft_engine = FastFFT(size=ctx.state.fft_size)
    raw_buf = bytearray(6)
    x_samps = array.array('i', [0] * 128)
    y_samps = array.array('i', [0] * 128)
    z_samps = array.array('i', [0] * 128)
    history = [0, 0, 0, 0, 0, 0]
    BAR_COLORS = (0xF800, 0xFD20, 0xFFE0, 0x07EA, 0x07E0)

    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit":
            break
        if act == "tap":
            history = [0, 0, 0, 0, 0, 0]

        # Dynamically adapt to active configuration
        cur_size = 32 if ctx.state.fft_size <= 32 else (64 if ctx.state.fft_size <= 64 else 128)
        if cur_size != fft_engine.size:
            fft_engine.set_size(cur_size)

        sample_delay = ctx.state.fft_sample_delay
        use_window = (ctx.state.fft_window == "hann")

        # High-speed I2C sampling loop (2ms - 5ms interval)
        for s in range(cur_size):
            if ctx.should_stop():
                return
            try:
                ctx.imu_service.read_raw_accel_into(raw_buf)
                x = (raw_buf[0] << 8) | raw_buf[1]
                if x >= 32768: x -= 65536
                y = (raw_buf[2] << 8) | raw_buf[3]
                if y >= 32768: y -= 65536
                z = (raw_buf[4] << 8) | raw_buf[5]
                if z >= 32768: z -= 65536

                x_samps[s] = x
                y_samps[s] = y
                z_samps[s] = z
            except Exception:
                pass
            await ctx.sleep_ms(sample_delay)

        # Process 3-axis FFT with DC-offset removal and optional windowing
        mag_x, mag_y, mag_z, total_e, half_n = fft_engine.process_3axis(
            x_samps, y_samps, z_samps, use_window=use_window
        )
        ctx.state.set_fft_data(total_e, mag_x, mag_y, mag_z, half_n=half_n)

        # Map normalized energy byte (0..255) directly to 6-column LED bar chart (0..5)
        e_byte = ctx.state.fft_bytes[1]
        if e_byte < 10: h = 0
        elif e_byte < 45: h = 1
        elif e_byte < 95: h = 2
        elif e_byte < 155: h = 3
        elif e_byte < 215: h = 4
        else: h = 5

        for c in range(5):
            history[c] = history[c + 1]
        history[5] = h

        ctx.matrix.fill(0)
        for col in range(6):
            height = history[col]
            for row in range(height):
                ctx.matrix.pixel(col, 4 - row, BAR_COLORS[4 - row])
        ctx.matrix.show()
