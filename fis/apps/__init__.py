from .base import BaseApp
from .config import App as ConfigApp
from .np_display import App as NeoPixelDisplayApp

try:
    import typing
except ImportError:
    typing = None

APPS = {
    'neopixel-display': NeoPixelDisplayApp,
}  # type: typing.Dict[str, typing.Type[BaseApp]]
