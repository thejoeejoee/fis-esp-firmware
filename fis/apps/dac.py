# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
import machine

from .base import BaseApp


class App(BaseApp):
    _dac = None

    async def init(self):
        port = int(self._config.get('port'))

        self._dac = machine.DAC(
            machine.Pin(port, mode=machine.Pin.OUT)
        )

    async def process(self, payload: dict, subtopics: list):
        value = payload.get('value')
        if value is not None:
            value = int(max(0., min(1., float(value))) * 190)
            self._dac.write(value)
            print("DAC: Value {} was written.".format(value))
