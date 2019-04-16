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
        self._interval = max((
            float(self._config.get('interval') or 0),
            self.MEASURE_EXPORT_DELAY
        )) - self.MEASURE_EXPORT_DELAY  # export
        # interval

        print('DHT: Scheduled measure')
        self._plan_app_task(self._run_measurement())

    async def _run_measurement(self):
        while True:
            try:
                self._dht.measure()
            except OSError as e:
                await self._error(
                    content="Failed to communicate with sensor: {}.".format(e),
                )
                await asyncio.sleep(self._interval)
                continue

            await asyncio.sleep(self.MEASURE_EXPORT_DELAY)
            await self._publish(dict(
                temperature=self._dht.temperature(),
                humidity=self._dht.humidity(),
            ), 'data')
            print('DHT: Rescheduled measure')
            await asyncio.sleep(self._interval)
