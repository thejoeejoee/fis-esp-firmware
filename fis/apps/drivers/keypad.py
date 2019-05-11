# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.

from machine import Pin
from uasyncio import sleep, get_event_loop


class KeypadDriver:
    # TODO: add also app
    def __init__(self, rows, cols):
        self._rows = [Pin(r) for r in rows]
        self._cols = [Pin(c) for c in cols]
        self.pressed = []

    async def scan(self):
        for p in self._cols + self._rows:
            p.init(Pin.IN, Pin.PULL_UP)

        for i_row, row in enumerate(self._rows):
            # set one row low at a time
            row.init(Pin.OUT)
            row.value(False)
            # check the column pins, which ones are pulled down
            for i_col, col in enumerate(self._cols):
                await sleep(.15)
                if not col.value():
                    print('row', i_row, 'col', i_col)
            # reset the pin to be an input
            row.init(Pin.IN, Pin.PULL_UP)


if __name__ == '__main__':
    d = KeypadDriver((13, 12, 14, 27), (26, 25, 33))


    async def read():
        while True:
            await sleep(.5)


    l = get_event_loop()
