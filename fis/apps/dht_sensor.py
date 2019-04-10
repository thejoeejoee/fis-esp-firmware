# coding=utf-8

import dht
import machine

from .base import BaseApp


class App(BaseApp):
    _dht = _scheduled = None

    async def init(self):
        self._dht = dht.DHT22(
            machine.Pin(
                int(self._config.get('port')),
            ),
        )
        await self.schedule(1, self._measure())
        print('DHT: Scheduled measure')

    def process(self, payload: dict):
        pass

    async def _measure(self):
        try:
            self._dht.measure()
        except OSError:
            print('DHT: Something wrong :-(')
            # TODO: publish status
            await self.schedule(10, self._measure())
            return

        await self.schedule(3, self._export_measure())
        print('DHT: Scheduled export')

    async def _export_measure(self):
        await self._publish(dict(
            temperature=self._dht.temperature(),
            humidity=self._dht.humidity(),
        ), 'data')
        await self.schedule(10, self._measure())
        print('DHT: Rescheduled measure')


if __name__ == '__main__':
    pass
