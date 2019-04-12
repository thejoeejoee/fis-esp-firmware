# coding=utf-8
import machine

from .base import BaseApp


class App(BaseApp):
    _dac = None

    def init(self):
        port = int(self._config.get('port'))

        self._dac = machine.DAC(
            machine.Pin(port, mode=machine.Pin.OUT)
        )

    def process(self, payload: dict, subtopics: list):
        if payload.get('value'):
            value = int(max(0., min(1., float(payload.get('value')))) * 190)
            self._dac.write(value)
            print("DAC: Value {} was written.".format(value))
