# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
import neopixel
import framebuf
import machine


class NeoPixelDisplay(framebuf.FrameBuffer):
    CHAR_WIDTH = 6

    def __init__(self, np, width, height, first_line_backward=False):
        self.width = width
        self.height = height
        self._buffer = bytearray(width * height)
        self._np = np
        self.first_line_backward = first_line_backward
        assert np.n == width * height
        super().__init__(
            self._buffer,
            self.width,
            self.height,
            framebuf.GS8
        )

    def show(self):
        backward_cmp = 0 if self.first_line_backward else 1
        self._np.fill((0, 0, 0))
        for i, color in enumerate(self._buffer):
            x = i % self.width
            y = i // self.width
            backward = (y % 2) == backward_cmp
            index = y * self.width + (self.width - x - 1 if backward else x)
            self._np[index] = self.color_to_rgb(color)
        self._np.write()

    def compact_text(self, text: str, x: int, y: int, color: int = 0b00100101):
        for i, s in enumerate(text):
            self.text(
                s,
                x - 1 + i * self.CHAR_WIDTH + i,
                y,
                color,
            )

    @staticmethod
    def color_to_rgb(color):
        return (
            ((0b111 << 5) & color) >> 5,
            ((0b111 << 2) & color) >> 2,
            2 * ((0b011 << 0) & color) >> 0,
        )

    @staticmethod
    def rgb_to_color(r, g, b):
        r = int((r / 255.) * 7)
        g = int((g / 255.) * 7)
        b = int((b / 255.) * 3)
        color = 0x00
        color |= ((r & 0b111) << 5)
        color |= ((g & 0b111) << 2)
        color |= ((b & 0b011) << 0)
        return color


if __name__ == '__main__':
    import random
    import time

    WIDTH = 27
    HEIGHT = 10

    BASE_COLORS = (
        0b00100000,
        0b00000100,
        0b00000001,

        0b00100001,
        0b00100100,
        0b00000101,
    )

    display = NeoPixelDisplay(
        neopixel.NeoPixel(
            machine.Pin(4, mode=machine.Pin.OUT),
            WIDTH * HEIGHT,
        ),
        WIDTH,
        HEIGHT,
        first_line_backward=True,
    )
    while True:
        display.fill(display.rgb_to_color(1, 1, 1))
        display.show()
        time.sleep_ms(500)

        display.fill(display.rgb_to_color(0, 0, 0))
        display.compact_text('JOE', 0, 1, random.choice(BASE_COLORS))
        display.show()
        time.sleep_ms(500)
