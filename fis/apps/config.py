from .base import BaseApp


class App(BaseApp):
    async def process(self, msg: dict, subtopics: list):
        app_id = subtopics[0]
        app_key = msg.get('app')
        config = msg.get('config')
        config.update(id=app_id)
        from . import APPS

        if app_id in self._core.apps:
            app = self._core.apps.get(app_id)
            app._config.update(config)
            await app.init()  # reinit
            print('CONF: New config {} ({}).'.format(app._config, app_id))

        elif app_key in APPS:
            app = self._core.apps[app_id] = APPS.get(app_key)(
                self._core,
                config,
            )
            await app.init()
            print('CONF: New app {} ({}).'.format(app_key, app_id))
        else:
            print('CONF: unknown {}.'.format(msg))
