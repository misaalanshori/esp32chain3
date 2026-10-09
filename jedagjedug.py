import time
import machine, neopixel

def wheel(pos):
    # Menghasilkan warna pelangi berdasarkan posisi input (0-255)
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

def demo(np):
    num_pixels = len(np)
    while True:
        for j in range(256):  # 256 warna dalam roda warna
            for i in range(num_pixels):
                pixel_index = (i + j) & 255
                np[i] = wheel(pixel_index & 255)
            np.write()
            time.sleep_ms(1)  # Sesuaikan kecepatan efek di sini
