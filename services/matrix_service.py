# services/matrix_service.py - NeoPixel Matrix Hardware Driver Service
import machine
import neopixel
from neomatrix import NeoMatrix

class MatrixService(NeoMatrix):
    def __init__(self, width=6, height=5, pin_id=7, brightness=0.3):
        self.pin = machine.Pin(pin_id, machine.Pin.OUT)
        self.np = neopixel.NeoPixel(self.pin, width * height)
        super().__init__(width, height, self.np)
        self.set_brightness(brightness)
