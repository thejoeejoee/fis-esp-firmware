import fis


class BaseApp(object):
    def __init__(self, core: "fis.Core", config: dict = None):
        self._config = config or {}
        self._core = core
        self._id = self._config.get('id')

    # TODO: consume also topic (or extracted information from topic)
    async def process(self, msg: dict, subtopics: list):
        raise NotImplementedError

    async def init(self):
        pass

    async def deinit(self):
        pass

    async def _publish(self, payload: dict, subtopic=None):
        return await self._core.publish(
            '/'.join(filter(None, ('app', self._id, subtopic))),
            payload
        )

    def _run_app_task(self, coro):
        return self._core.run_app_task(
            for_app=self,
            coro=coro
        )

    @property
    def id(self):
        return self._id