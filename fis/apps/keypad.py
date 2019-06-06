# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.

import dht
import machine

from .base import BaseApp
import uasyncio as asyncio


class App(BaseApp):
    _rows = _cols = None
    MEASURE_EXPORT_DELAY = 3

    async def init(self):
        self._rows = []
        await self._plan_app_task(self._run())

    async def _run(self):
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
