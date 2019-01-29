# coding=utf-8

import dht
import machine

from .base import BaseApp


class App(BaseApp):
    _dht = _scheduled = None

    def init(self):
        self._dht = dht.DHT22(
            machine.Pin(
                int(self._config.get('port')),
            ),
        )
        self.schedule(0, self._measure)
        print('DHT: Scheduled measure')

    def process(self, payload: dict):
        pass

    def _measure(self):
        try:
            self._dht.measure()
        except OSError:
            print('DHT: Something wrong :-(')
            # TODO: publish status
            self.schedule(10, self._measure)
            return

        self.schedule(3, self._export_measure)
        print('DHT: Scheduled export')

    def _export_measure(self):
        self._publish(dict(
            temperature=self._dht.temperature(),
            humidity=self._dht.humidity(),
        ), 'data')
        self.schedule(10, self._measure)
        print('DHT: Rescheduled measure')


if __name__ == '__main__':
    pass
