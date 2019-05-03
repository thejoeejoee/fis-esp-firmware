# coding=utf-8

import uasyncio as asyncio

import esp
import micropython

from fis.apps.base import BaseApp

micropython.alloc_emergency_exception_buf(128)
esp.osdebug(None)

try:
    import typing
except ImportError:
    typing = None

from .mqtt_connection import MQTTConnection
import json

import time
import machine
import binascii
from .apps.config import App as ConfigApp

if typing:
    from asyncio import AbstractEventLoop

CONFIG_FILE = 'config.json'


class Core:
    def __init__(self):
        with open(CONFIG_FILE) as f:
            self._config = json.loads(f.read())

        # self._adc = machine.ADC(machine.Pin(34))
        # self._adc.atten(self._adc.ATTN_11DB)  # 150 to 1750mV

        self._id = binascii.hexlify(machine.unique_id()).decode()
        self._base_publish_topic = 'fis/from/{}'.format(self._id)
        self._base_subscribe_topic = 'fis/to/{}'.format(self._id)
        print('\nCORE: node ID: {}\n'.format(self._id))

        self.apps = dict(
            config=ConfigApp(self),
        )  # type: typing.Dict[str, BaseApp]
        self._apps_tasks = dict()  # type: typing.Dict[str, asyncio.Corutine]

        self._status_led = machine.Signal(machine.Pin(2, machine.Pin.OUT))

        # last will message used for offline notification
        last_will = [
            '{}/status'.format(self._base_publish_topic),
            json.dumps(dict(online=False)),
            True,
            1
        ]
        self._connection = MQTTConnection(
            status_led=self._status_led,
            wifi_creds=self._config.get('wlans'),
            client_id='esp-{}'.format(self._id),
            user=self._config.get('broker-username'),
            password=self._config.get('broker-password'),
            server=self._config.get('broker'),
            will=last_will,
            keepalive=30,  # TODO ?
            wifi_coro=self._on_wifi_state_change,
            connect_coro=self._on_estabilished_connection,
            subs_cb=self._on_message_sync,
        )
        self._connection.DEBUG = True

        # 64 running tasks queue capacity, 64 waiting tasks queue capacity,
        self._loop = asyncio.get_event_loop(64, 64)  # type: AbstractEventLoop

    def start(self):
        """
        Blocking start of firmware core.
        """
        print('\nCORE: node ID: {}\n'.format(self._id))
        self._loop.create_task(self._run())
        self._loop.run_forever()

    def run_app_task(self, for_app: BaseApp, coro: "typing.Awaitable" = None):
        """
        Plan task for given app - already existing app task is cancelled.
        Method called from app instances to start app loop.
        If no coro is given, task is only removed, not planned.
        """
        existing_coro = self._apps_tasks.get(for_app.id)
        if existing_coro:
            asyncio.cancel(existing_coro)
            del self._apps_tasks[for_app.id]

        if not coro:
            return None
        self._loop.create_task(coro)

        self._apps_tasks[for_app.id] = coro
        return coro

    async def publish(self, subtopic: str, payload: dict, retain: bool = False):
        """
        Publish given message in subtopic (related to base publish topic).
        :param subtopic: specific subtopic (without /fis/from/...)
        :param payload: message as dict
        :param retain: should be this message retained?
        """
        self._status_led.on()
        topic = '{}/{}'.format(
            self._base_publish_topic,
            subtopic.strip('/')
        )
        print('CORE: publish ./{}: {}'.format(subtopic, payload))
        # TODO: check connection, if not ok, store message in temp list and send them after reconnection
        await self._connection.publish(
            topic.encode(),
            json.dumps(payload) if payload is not None else '',
            qos=1,
            retain=retain,
        )
        self._status_led.off()

    async def _run(self):
        """
        Main loop - nearly empty, because all of magic, after connection, happens in _on_message coroutine.
        """

        self._status_led.on()
        try:
            await self._connection.connect()
        except OSError as e:
            print('Connection failed: {}.'.format(str(e)))
            return
        self._status_led.off()

    async def _on_wifi_state_change(self, state):
        """Save config with known wlans after succesfull connection to WLAN."""
        if state:
            self._save_config()  # save reordered wlans
        else:
            self._status_led.on()

    async def _on_estabilished_connection(self, connection: MQTTConnection):
        """After broker connection is estabilished, subscribe main channel and publish node status."""
        await self._connection.subscribe('{}/#'.format(self._base_subscribe_topic).encode())
        await self.publish('status', dict(online=True), retain=True)  # hello there!

    def _on_message_sync(self, topic, payload, retained):
        """Callback version of message processor - used for MQTTConnection."""
        return self._loop.create_task(
            self._on_message(topic, payload, retained)
        )

    async def _on_message(self, topic: bytes, payload: bytes, retained: bool):
        """Coroutine version of message callback. """
        self._status_led.on()
        topic = topic.decode()
        try:
            payload = json.loads(payload)  # type: dict
        except ValueError:
            if payload:
                print('CORE: error during message parsing: {}.'.format(payload))
            else:
                # retain reset is empty message
                self._status_led.off()
                return

        local_subtopic = topic[len(self._base_subscribe_topic):].lstrip('/')
        print('CORE: message in ./{}: {}.'.format(local_subtopic, payload))

        main_subtopic, *subtopic_args = local_subtopic.split('/')
        if main_subtopic == 'app' and subtopic_args:
            # message for some of app
            app_id = subtopic_args[0]
            app = self.apps.get(app_id)
            if not app:
                pass  # TODO: (retained) message maybe come to early, so store it and wait for app config

            try:
                await app.process(
                    payload.get('payload'),
                    subtopic_args[1:]  # exclude first app_id
                )
            except Exception as e:
                await self.log(
                    content="Exception during message processing: '{}'.".format(str(e)),
                    level=BaseApp.LOG_ERROR,
                    app_id=app_id
                )
        else:
            await self.log(
                content="Unable to proccess message '{}'.".format(str(payload)),
                level=BaseApp.LOG_ERROR,
            )

        # self.publish('ack', {})
        self._status_led.off()

    async def log(self, content, level, app_id=None):
        """Logs custom message on given level to MQTT. With app_id given, the app channel is used, otherwise
        node-specific topic is used."""
        msg = dict(
            level=level,
            content=content,
        )
        if app_id:
            topic = 'app/{}/log'.format(app_id)
        else:
            topic = 'log'

        await self.publish(
            subtopic=topic,
            payload=msg,
        )

    def _save_config(self):
        """Saves actual config from memory to config file."""
        with open(CONFIG_FILE, 'w') as f:
            f.write(json.dumps(self._config))
