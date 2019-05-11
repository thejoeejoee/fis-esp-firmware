# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
from .base import BaseApp
from .config import App as ConfigApp
from .dht_sensor import App as DHTSensorApp
from .np_display import App as NeoPixelDisplayApp
from .dac import App as DACApp

try:
    import typing
except ImportError:
    typing = None

APPS = {
    'neopixel-display': NeoPixelDisplayApp,
    'dht-sensor': DHTSensorApp,
    'dac': DACApp,
}  # type: typing.Dict[str, typing.Type[BaseApp]]
