import fis


class BaseApp(object):
    def __init__(self, core: "fis.Core", config: dict = None):
        self._config = config or {}
        self._core = core
        self._id = self._config.get('id')

    def process(self, msg: dict):
        raise NotImplementedError

    async def init(self):
        pass

    async def _publish(self, payload: dict, subtopic=None):
        return await self._core.publish(
            '/'.join(filter(None, ('app', self._id, subtopic))),
            payload
        )

    async def schedule(self, in_time, action):
        return await self._core.schedule(
            for_app=self,
            delay=in_time,
            action=action
        )
