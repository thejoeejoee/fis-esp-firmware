from .base import BaseApp

import uasyncio as asyncio


class App(BaseApp):
    ACTION_INIT = 'init'
    ACTION_REMOVE = 'remove'

    async def process(self, msg: dict, subtopics: list):
        config = msg.get('config')
        action = msg.get('action')
        app_id = subtopics[0]
        from . import APPS

        # initialization or reinitialization
        if action == self.ACTION_INIT:
            config.update(id=app_id)
            app_key = msg.get('app')
            app = None

            # already existing app
            if app_id in self._core.apps:
                app = self._core.apps.get(app_id)
                app.config.update(config)
                print('CONF: New config {} ({}).'.format(app._config, app_id))

            # new app
            elif app_key in APPS:
                app = self._core.apps[app_id] = APPS.get(app_key)(
                    self._core,
                    config,
                )
                print('CONF: New app {} ({}).'.format(app_key, app_id))
            else:
                pass  # TODO what?

            if not app:
                return

            try:
                app._plan_app_task(coro=None)  # reset planned task
                await app.init()
            except Exception as e:
                await self._error(
                    content="Error during app {} init with config '{}': '{}'".format(
                        app_key,
                        app.config,
                        str(e)
                    ),
                    app_id=app_id,  # ERROR of specific app, not error of ConfigApp
                )

        # removing app
        elif action == self.ACTION_REMOVE:
            if app_id in self._core.apps:
                app = self._core.apps.get(app_id)
                app._plan_app_task(coro=None)
                app.deinit()
                del self._core.apps[app_id]
                if app_id in self._core._apps_tasks:
                    asyncio.cancel(self._core._apps_tasks.get(app_id))

        else:
            print('CONF: unknown {}.'.format(msg))
