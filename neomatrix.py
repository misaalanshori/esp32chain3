import framebuf

FIVERATIO = const(8) # 255 // 31
SIXRATIO = const(4) # 255 // 63

class NeoMatrix(framebuf.FrameBuffer):
    def __init__(self, width, height, neopixel, gamma = 2.8):
        self.width = width
        self.height = height
        self.length = self.height * self.width
        self.buffer = bytearray(self.length * 2)
        self.neopixel = neopixel
        self.brightness = 1
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.gamma_lut = bytearray(256)
        self.set_gamma(gamma)
        self.init_display()

    def init_display(self):
        self.fill(0)
        self.show()

    def set_brightness(self, brightness):
        self.brightness = brightness

    def set_gamma(self, gamma):
        self.gamma_lut = bytearray([int((i / 255) ** gamma * 255) for i in range(256)])

    @micropython.viper
    def __neopixel_draw(self, brightness: int):
        framebuf = ptr8(self.buffer)
        framebuf_len = int(len(self.buffer))
        neobuf = ptr8(self.neopixel.buf)
        gammalut = ptr8(self.gamma_lut)
        width = int(self.width)
        
        buffer_index = 0
        for i in (range(0, framebuf_len, 2)):
            # Read two bytes and form a 16-bit RGB565 value
            itr = int(i)
            rgb565 = (framebuf[itr + 1] << 8) | framebuf[itr]

            # Extract and scale RGB components
            r = ((rgb565 >> 11) & 0x1F) * FIVERATIO
            g = ((rgb565 >> 5) & 0x3F) * SIXRATIO
            b = (rgb565 & 0x1F) * FIVERATIO

            line_number = (buffer_index//width)+1
            
            npIndex = buffer_index
            if (not (line_number & 1)):
                line_index = buffer_index%width
                npIndex = line_number*width - line_index - 1
                
            npIndex *= 3 # BPP
            
            # Because of GRB(W) ORDER = (1, 0, 2, 3)
            neobuf[npIndex + 1] = (((gammalut[r] * 1000) * brightness) // 1000000)
            neobuf[npIndex + 0] = (((gammalut[g] * 1000) * brightness) // 1000000)
            neobuf[npIndex + 2] = (((gammalut[b] * 1000) * brightness) // 1000000)

            buffer_index += 1

    @micropython.native
    def show(self):
        self.__neopixel_draw(
            int(self.brightness * 1000)
        )
        self.neopixel.write()


