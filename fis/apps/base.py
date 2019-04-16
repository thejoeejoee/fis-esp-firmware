import fis


class BaseApp(object):
    """
    Base parent for all apps - supports config management, app lifecycle and publish.
    """

    LOG_ERROR = 'error'
    LOG_INFO = 'info'

    def __init__(self, core: "fis.Core", config: dict = None):
        self._config = config or {}
        self._core = core

    async def process(self, msg: dict, subtopics: list):
        """Process comming message in given local subtopic. Children class should overwrite it."""
        raise NotImplementedError

    async def init(self):
        """Entry point for app lifecycle - app should initializate drivers."""
        pass

    async def deinit(self):
        """End part of app lifecycle - app should deinitializate drivers."""
        pass

    async def _publish(self, payload: dict, subtopic=None):
        """Publish into app subchannel - optionaly with given subtopic."""
        return await self._core.publish(
            '/'.join(filter(None, ('app', self.id, subtopic))),
            payload
        )

    async def _log(self, content, level, app_id=None):
        await self._core.log(
            content=content,
            level=level,
            app_id=app_id or self.id,
        )

    def _plan_app_task(self, coro=None):
        """Asks core for start app corutine."""
        return self._core.run_app_task(
            for_app=self,
            coro=coro
        )

    @property
    def config(self):
        return self._config

    @property
    def id(self):
        return self.config.get('id')
