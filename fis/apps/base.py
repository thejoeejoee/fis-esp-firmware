# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
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
        """Process comming message in given local subtopic. Children class receiving data should overwrite it."""
        pass

    async def init(self):
        """Entry point for app lifecycle - app should initializate drivers."""
        pass

    async def deinit(self):
        """End part of app lifecycle - app should deinitializate drivers."""
        pass

    async def _publish(self, payload: dict, subtopic=None, retain=False):
        """Publish into app subchannel - optionaly with given subtopic."""
        return await self._core.publish(
            subtopic='/'.join(filter(None, ('app', self.id, (subtopic or '').strip('/')))),
            payload=payload,
            retain=retain
        )

    async def _error(self, content, app_id=None):
        return await self._log(content=content, app_id=app_id, level=self.LOG_ERROR)

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
