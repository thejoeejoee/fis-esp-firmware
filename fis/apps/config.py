from .base import BaseApp


class App(BaseApp):
    def process(self, msg: dict):
        app_id = msg.get('app_id')
        app_key = msg.get('app')
        config = msg.get('config')
        config.update(id=app_id)
        from . import APPS

        if app_id in self._core.apps:
            app = self._core.apps.get(app_id)
            app._config.update(config)
            app.init()  # reinit
            print('CONF: New config {} ({}).'.format(app._config, app_id))

        elif app_key in APPS:
            app = self._core.apps[app_id] = APPS.get(app_key)(
                self._core,
                config,
            )
            app.init()
            print('CONF: New app {} ({}).'.format(app_key, app_id))
        else:
            print('CONF: unknown {}.'.format(msg))
