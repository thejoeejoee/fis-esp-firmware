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

from umqtt.simple import MQTTClient  # TODO: custom mqtt class, robust is bullshit

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

        self.apps = dict(
            config=ConfigApp(self),
        )  # type: typing.Dict[str, BaseApp]
        self._apps_tasks = dict()  # type: typing.Dict[str, asyncio.Corutine]

        self._status_led = machine.Signal(machine.Pin(2, machine.Pin.OUT))

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
            server="fis.josefkolar.cz",
            will=last_will,
            keepalive=30,  # TODO ?
            wifi_coro=self._on_wifi_state_change,
            connect_coro=self._on_estabilished_connection,
            subs_cb=self._on_message_sync,
        )
        self._connection.DEBUG = True

        self._loop = asyncio.get_event_loop()  # type: AbstractEventLoop

    def start(self):
        """
        Blocking start of firmware core.
        """
        self._loop.run_until_complete(self._run())

    async def _run(self):
        """
        Main loop - nearly empty, because all of magic, after connection, happens in _on_message coroutine.
        """
        try:
            await self._connection.connect()
        except OSError as e:
            print('Connection failed: {}.'.format(str(e)))
            return

        while True:
            await asyncio.sleep(5)

    def run_app_task(self, for_app: BaseApp, coro: "typing.Awaitable"):
        """
        Plan task for given app - already existing app task is cancelled.
        """
        existing_coro = self._apps_tasks.get(for_app.id)
        if existing_coro:
            asyncio.cancel(existing_coro)

        self._loop.create_task(coro)

        self._apps_tasks[for_app.id] = coro
        return coro

    async def _on_wifi_state_change(self, state):
        """Save config with known wlans after succesfull connection to WLAN."""
        if state:
            self.save_config()  # save reordered wlans

    async def _on_estabilished_connection(self, connection: MQTTConnection):
        """After broker connection is estabilished, subscribe main channel and publish node status."""
        await self._connection.subscribe('{}/#'.format(self._base_subscribe_topic).encode())
        await self.publish('status', dict(online=True), retain=True)

    def _on_message_sync(self, topic, payload, retained):
        """Callback version of message processor - used for MQTTConnection."""
        return self._loop.create_task(
            self._on_message(topic, payload, retained)
        )

    async def _on_message(self, topic: bytes, payload: bytes, retained: bool):
        """Corotunie version of message callback. """
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
            await app.process(
                payload.get('payload'),
                subtopic_args[1:]  # exclude first app_id
            )

        else:
            print('CORE: Unable to process message {}.'.format(payload))

        # self.publish('ack', {})
        self._status_led.off()

    async def publish(self, subtopic: str, payload: dict, retain: bool = False):
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

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            f.write(json.dumps(self._config))

    def __del__(self):
        self._wlan.__del__()
