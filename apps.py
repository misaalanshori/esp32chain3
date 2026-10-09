# apps.py - Built-in applications for 6x5 NeoMatrix
import machine
import time
from menu import check_exit
from state import system_state

MATRIX_WIDTH = const(6)
MATRIX_HEIGHT = const(5)

@micropython.native
def hsv_to_rgb(h, s, v):
    h = h % 360
    i = int(h * 0.016)
    f = (h * 0.016) - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    return int(r * 255), int(g * 255), int(b * 255)

def rgb_to_rgb565(r, g, b):
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5

def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# --- App 1: Animated Rainbow ---
def app_rainbow(matrix, btn):
    offset = 0
    while not check_exit(btn):
        for x in range(MATRIX_WIDTH):
            for y in range(MATRIX_HEIGHT):
                h = ((x + y) * 36 + offset) % 360
                r, g, b = hsv_to_rgb(h, 0.9, 0.4)
                matrix.pixel(x, y, rgb_to_rgb565(r, g, b))
        matrix.show()
        offset = (offset + 12) % 360
        time.sleep_ms(25)

# --- App 2: Jedag-Jedug (Color Wheel) ---
def app_jedagjedug(matrix, btn):
    np = matrix.neopixel
    num_pixels = len(np)
    j = 0
    while not check_exit(btn):
        for i in range(num_pixels):
            np[i] = wheel((i * 8 + j) & 255)
        np.write()
        j = (j + 4) & 255
        time.sleep_ms(20)

# --- App 3: MPU6050 Bubble Level ---
def app_bubble(matrix, btn):
    try:
        from MPU6050 import MPU6050
        mpu_pwr = machine.Pin(2, machine.Pin.OUT)
        mpu_pwr.value(1)
        time.sleep_ms(50)
        i2c = machine.SoftI2C(scl=machine.Pin(4), sda=machine.Pin(3))
        mpu = MPU6050(i2c=i2c)
    except Exception as e:
        print("IMU init failed:", e)
        return

    while not check_exit(btn):
        try:
            acc = mpu.read_accel_data()
            ax = acc["x"]
            ay = acc["y"]
            az = acc["z"]
            temp = mpu.read_temperature()
            system_state.set_sensor(ax, ay, az, temp)

            bx = min(5, max(0, int(round(2.5 + (ax / 9.8) * 2.5))))
            by = min(4, max(0, int(round(2.0 + (ay / 9.8) * 2.0))))

            matrix.fill(0)
            # Center target crosshair
            matrix.pixel(2, 2, 0x18C3)
            matrix.pixel(3, 2, 0x18C3)

            # Bubble color based on tilt deviation
            if (bx in (2, 3)) and by == 2:
                color = 0x07E0  # Green: level
            elif (bx in (1, 4)) or (by in (1, 3)):
                color = 0xFFE0  # Yellow: slight tilt
            else:
                color = 0xF800  # Red: steep tilt

            matrix.pixel(bx, by, color)
            matrix.show()
        except Exception:
            pass
        time.sleep_ms(40)

REGISTERED_APPS = (
    ("Rainbow", app_rainbow),
    ("JedagJedug", app_jedagjedug),
    ("BubbleLevel", app_bubble),
)
