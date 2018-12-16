from .np_display import App as NeoPixelDisplayApp

REGISTRY = {
    "neopixel-display": NeoPixelDisplayApp(config=dict()),
}
