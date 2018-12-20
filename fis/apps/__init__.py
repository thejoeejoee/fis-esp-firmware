from .base import BaseApp
from .config import App as ConfigApp
from .dht_sensor import App as DHTSensorApp
from .np_display import App as NeoPixelDisplayApp

try:
    import typing
except ImportError:
    typing = None

APPS = {
    'neopixel-display': NeoPixelDisplayApp,
    'dht-sensor': DHTSensorApp,
}  # type: typing.Dict[str, typing.Type[BaseApp]]
