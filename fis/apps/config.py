from .base import BaseApp

import uasyncio as asyncio
import machine


class App(BaseApp):
    ACTION_INIT = 'init'
    ACTION_REMOVE = 'remove'
    ACTION_DEPLOY_FILE = 'deploy'
    ACTION_RESET = 'reset'

    async def process(self, msg: dict, subtopics: list):
        action = msg.get('action')
        from . import APPS

        # initialization or reinitialization
        if action == self.ACTION_INIT:
            app_id = subtopics[0]
            config = msg.get('config')
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
            app_id = subtopics[0]
            if app_id in self._core.apps:
                app = self._core.apps.get(app_id)
                app._plan_app_task(coro=None)
                app.deinit()
                del self._core.apps[app_id]

        # deploy new file
        elif action == self.ACTION_RESET:
            machine.reset()


        else:
            print('CONF: unknown {}.'.format(msg))
