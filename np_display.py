# coding=utf-8
import framebuf
import machine
import neopixel


class NeoPixelDisplay(framebuf.FrameBuffer):
    def __init__(self, np, width, height, first_backward=False):
        self.width = width
        self.height = height
        self.buffer = bytearray(width * height)
        self.np = np
        self.first_backward = first_backward
        assert np.n == width * height
        super().__init__(
            self.buffer,
            self.width,
            self.height,
            framebuf.GS8
        )

    def show(self):
        backward_cmp = 0 if self.first_backward else 1
        self.np.fill((0, 0, 0))
        for i, v in enumerate(self.buffer):
            x = i % self.width
            y = i // self.width
            backward = (y % 2) == backward_cmp
            index = y * self.width + (self.width - x - 1 if backward else x)
            self.np[index] = (5, 0, 0) if v else (0, 0, 0)
        self.np.write()


if __name__ == '__main__':
    WIDTH = 27
    HEIGHT = 10

    display = NeoPixelDisplay(
        neopixel.NeoPixel(
            machine.Pin(4, mode=machine.Pin.OUT),
            WIDTH * HEIGHT,
        ),
        WIDTH,
        HEIGHT
    )

    display.text("w", -1, 0)
    display.text("y", 6 + 1, 0)
    display.text("k", 6 + 6 + 1 + 1, 0)
    display.text("y", 6 + 6 + 6 + 1 + 1 + 1, 0)
    display.hline(0, 9, 27, 1)
    display.show()
