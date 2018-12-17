import fis


class BaseApp(object):
    def __init__(self, core: "fis.Core", config: dict = None):
        self._config = config or {}
        self._core = core

    def process(self, msg: dict):
        raise NotImplementedError

    def init(self):
        pass
