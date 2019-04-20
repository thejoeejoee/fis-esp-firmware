# coding=utf-8
import machine
import neopixel

from .drivers.neopixel_display import NeoPixelDisplay
from .base import BaseApp


class App(BaseApp):
    _display = _color = None

    async def init(self):
        width = int(self._config.get('width'))
        height = int(self._config.get('height'))

        self._display = NeoPixelDisplay(
            neopixel.NeoPixel(
                machine.Pin(
                    int(self._config.get('port')),
                    mode=machine.Pin.OUT
                ),
                width * height,
            ),
            width,
            height,
            first_line_backward=True,
        )
        self._color = self._color or 0b00100101

    async def process(self, payload: dict, subtopics: list):
        if payload.get('color'):
            self._color = self._display.rgb_to_color(*payload.get('color'))

        if payload.get('text'):
            self._display.fill(0)
            self._display.compact_text(
                payload.get('text'),
                0,
                1,
                self._color,
            )
            self._display.show()
