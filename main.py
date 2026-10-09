from neomatrix import NeoMatrix
import neopixel
import machine
import time
import gc
import framebuf

matrixWidth = const(6)
matrixHeight = const(5)

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
    # Convert 8-bit RGB to 5-bit (R), 6-bit (G), and 5-bit (B)
    r5 = (r >> 3) & 0x1F  # 8-bit to 5-bit
    g6 = (g >> 2) & 0x3F  # 8-bit to 6-bit
    b5 = (b >> 3) & 0x1F  # 8-bit to 5-bit

    # Combine into a single 16-bit integer
    return (r5 << 11) | (g6 << 5) | b5
        
def fill_rainbow(framebuffer, width, height):
    total = width + height - 1
    for x in range(width):
        for y in range(height):
            step = x + y
            h = (step / total) * 360
            r, g, b = hsv_to_rgb(h, 0.2, 0.5)
            color = rgb_to_rgb565(r, g, b)
            framebuffer.pixel(x, y, color)        

def main(iterations=60):
    neo_pin = machine.Pin(7, machine.Pin.OUT)
    neo_pixel = neopixel.NeoPixel(neo_pin, matrixWidth*matrixHeight)
    neo_matrix = NeoMatrix(matrixWidth, matrixHeight,neo_pixel)
    neo_matrix.set_brightness(1)
    
    rainbowbg = framebuf.FrameBuffer(bytearray(matrixWidth*matrixHeight*2), matrixWidth, matrixHeight, framebuf.RGB565)
    fill_rainbow(rainbowbg, matrixWidth, matrixHeight)
    gc.disable()
    while True:
        neo_matrix.blit(rainbowbg, 0, 0)
        neo_matrix.show()

if __name__ == "__main__":
    main()