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

        self._id = binascii.hexlify(machine.unique_id())
        self._base_publish_topic = 'fis/from/{}'.format(self._id.decode())
        self._base_subscribe_topic = 'fis/to/{}'.format(self._id.decode())

        self.apps = dict(
            config=ConfigApp(self),
        )  # type: typing.Dict[str, BaseApp]

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
            client_id=self._id,
            server="fis.josefkolar.cz",
            will=last_will,
            keepalive=0,  # TODO ?
            wifi_coro=self._on_wifi_state_change,
            connect_coro=self._on_estabilished_connection,
            subs_cb=self._on_message_sync,
        )
        self._connection.DEBUG = True

        self._loop = asyncio.get_event_loop()  # type: AbstractEventLoop

    def start(self):
        self._loop.run_until_complete(self._run())

    async def _run(self):
        try:
            await self._connection.connect()
        except OSError:
            print('Connection failed.')
            return
        n = 0
        while True:
            await asyncio.sleep(5)
            print('loop')
            # loop here

    async def schedule(self, for_app: BaseApp, delay: int, action: "typing.Callable"):
        task = self._loop.call_later(
            delay=delay,
            callback=action
        )

        return task

    async def _on_wifi_state_change(self, state):
        if state:
            self.save_config()  # save reordered wlans

    async def _on_estabilished_connection(self, connection: MQTTConnection):
        await self._connection.subscribe('{}/#'.format(self._base_subscribe_topic).encode())
        await self.publish('status', dict(online=True))

    def _on_message_sync(self, topic, payload, retained):
        return self._loop.call_soon(
            asyncio.ensure_future(
                self._on_message(topic, payload, retained)
            )
        )

    async def _on_message(self, topic: bytes, payload: bytes, retained: bool):
        self._status_led.on()
        topic = topic.decode()
        try:
            payload = json.loads(payload)  # type: dict
        except ValueError:
            if not payload:  # retain reset is empty message
                print('CORE: error during message parsing: {}.'.format(payload))
                self._status_led.off()

        print('CORE: message in {}: {}.'.format(topic, payload))

        app = self.apps.get(payload.get('app_id'))

        if app:
            await app.process(payload.get('payload'))
        else:
            print('CORE: Unknown app with app_id={}.'.format(payload.get('app_id')))

        # self.publish('ack', {})
        self._status_led.off()

    async def publish(self, subtopic: str, payload: dict, retain: bool = False):
        topic = '{}/{}'.format(
            self._base_publish_topic,
            subtopic.strip('/')
        )
        print('CORE: publish {} {}'.format(topic, payload))
        await self._connection.publish(
            topic.encode(),
            json.dumps(payload) if payload is not None else '',
            qos=1,
            retain=retain,
        )  # TODO: qos=1 wants wait_message

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            f.write(json.dumps(self._config))

    def __del__(self):
        self._wlan.__del__()
