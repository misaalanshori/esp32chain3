# apps/mpu_fft.py - App 13: High-Speed 3-Axis FFT & Energy Waterfall
import array
from fft import FastFFT32

async def app_fft(ctx):
    imu = ctx.get_imu()
    if not imu:
        return

    fft_engine = FastFFT32()
    raw_buf = bytearray(6)
    x_samps = array.array('i', [0] * 32)
    y_samps = array.array('i', [0] * 32)
    z_samps = array.array('i', [0] * 32)
    history = [0, 0, 0, 0, 0, 0]
    BAR_COLORS = (0xF800, 0xFD20, 0xFFE0, 0x07EA, 0x07E0)

    while not ctx.should_stop():
        act = ctx.poll_action(ctx.app_manager.button)
        if act == "exit":
            break
        if act == "tap":
            history = [0, 0, 0, 0, 0, 0]

        # Fast 3ms sampling (~300 Hz sample rate, < 5ms interval)
        for s in range(32):
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
            await ctx.sleep_ms(3)

        # 3-Axis FFT with DC offset removal and Hanning window
        mag_x, mag_y, mag_z, total_e = fft_engine.process_3axis(x_samps, y_samps, z_samps)
        ctx.state.set_fft_data(total_e, mag_x, mag_y, mag_z)

        # Dynamic movement energy mapped to bar height 0..5
        if total_e < 1200: h = 0
        elif total_e < 3500: h = 1
        elif total_e < 8000: h = 2
        elif total_e < 16000: h = 3
        elif total_e < 30000: h = 4
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
