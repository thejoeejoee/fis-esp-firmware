# coding=utf-8

import dht
import machine

from .base import BaseApp
import uasyncio as asyncio


class App(BaseApp):
    _dht = None
    _interval = 10
    MEASURE_EXPORT_DELAY = 3

    async def init(self):
        self._dht = dht.DHT22(
            machine.Pin(
                int(self._config.get('port')),
            ),
        )
        self._interval = max((float(self._config.get('interval') or 0), 3)) - 3  # export interval

        print('DHT: Scheduled measure')
        self._run_app_task(self._run_measurement())

    async def process(self, payload: dict, subtopics: list):
        pass

    async def _run_measurement(self):
        while True:
            try:
                self._dht.measure()
            except OSError:
                print('DHT: Something wrong :-(')
                # TODO: publish log with fail
                await asyncio.sleep(self._interval)
                continue

            await asyncio.sleep(self.MEASURE_EXPORT_DELAY)
            await self._publish(dict(
                temperature=self._dht.temperature(),
                humidity=self._dht.humidity(),
            ), 'data')
            print('DHT: Rescheduled measure')
            await asyncio.sleep(self._interval)


if __name__ == '__main__':
    pass
