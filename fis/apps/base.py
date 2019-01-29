import fis


class BaseApp(object):
    def __init__(self, core: "fis.Core", config: dict = None):
        self._config = config or {}
        self._core = core
        self._id = self._config.get('id')

    def process(self, msg: dict):
        raise NotImplementedError

    def init(self):
        pass

    def _publish(self, payload: dict, subtopic=None):
        return self._core.publish(
            '/'.join(filter(None, ('app', self._id, subtopic))),
            payload
        )

    def schedule(self, in_time, action):
        return self._core.schedule(
            for_app=self,
            in_time=in_time,
            action=action
        )
