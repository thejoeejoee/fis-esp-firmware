# coding=utf-8
import esp
import micropython

from fis.apps.base import BaseApp

micropython.alloc_emergency_exception_buf(128)
esp.osdebug(None)

try:
    import typing
except ImportError:
    typing = None

from .wlan import WLAN
import json

from umqtt.simple import MQTTClient # TODO: custom mqtt class, robust is bullshit

import time
import machine
import binascii
from .apps.config import App as ConfigApp

CONFIG_FILE = 'config.json'


class Core:
    def __init__(self):
        with open(CONFIG_FILE) as f:
            self._config = json.loads(f.read())

        self._wlan = WLAN(self._config.get('wlans'))
        self._adc = machine.ADC(machine.Pin(34))
        self._adc.atten(self._adc.ATTN_11DB)  # 150 to 1750mV

        self._id = binascii.hexlify(machine.unique_id())
        self._mqtt = MQTTClient(self._id, "fis.josefkolar.cz", keepalive=10)  # TODO: to config
        self._mqtt.DEBUG = True
        self._base_publish_topic = 'fis/from/{}'.format(self._id.decode())
        self._base_subscribe_topic = 'fis/to/{}'.format(self._id.decode())

        self.apps = dict(
            config=ConfigApp(self),
        )  # type: typing.Dict[str, BaseApp]
        self._scheduled_actions = []  # type: typing.List[typing.Tuple[int, typing.Callable]]

        self._status_led = machine.Signal(machine.Pin(2, machine.Pin.OUT))

    def start(self):
        self._wlan.connect()

        while not self._wlan.is_connected:
            self._status_led.on()
            time.sleep_ms(100)
            self._status_led.off()
            time.sleep_ms(100)

        self._status_led.on()

        self.save_config()  # save reordered wlans

        # TODO: last will
        # TODO: session clean?

        last_will_topic = '{}/status'.format(self._base_publish_topic)
        self._mqtt.set_last_will(last_will_topic, json.dumps(dict(online=False)), retain=False, qos=2)

        self._mqtt.connect(clean_session=False)
        self._mqtt.set_callback(self._on_message)
        self._mqtt.subscribe('{}/#'.format(self._base_subscribe_topic).encode())

        self.publish('status', dict(online=True))

        print('CORE: subscribed to {}/#.'.format(self._base_subscribe_topic))
        self._status_led.off()

        while True:
            try:
                self._mqtt.check_msg()
            except OSError as e:
                if e.errno != -1:
                    raise e

            now = time.time()
            print('CORE: loop for {}, planned {}.'.format(now, len(self._scheduled_actions)))

            for action in filter(
                    lambda act: act[0] <= now,  # older or equal to now
                    self._scheduled_actions
            ):
                _, action_cb = action
                action_cb()
                self._scheduled_actions.remove(action)

            time.sleep(1)  # 1 sec loop

            # v = self._adc.read()

    def schedule(self, in_time: int, action: "typing.Callable"):
        at = int(time.time() + in_time)
        # TODO: only one scheduled by app?
        self._scheduled_actions.append((at, action))

    def _on_message(self, topic: bytes, payload: bytes):
        self._status_led.on()
        topic = topic.decode()
        payload = json.loads(payload)  # type: dict
        print('CORE: message in {}: {}.'.format(topic, payload))

        app = self.apps.get(payload.get('app_id'))

        if app:
            app.process(payload.get('payload'))
        else:
            print('CORE: Unknown app with app_id={}.'.format(payload.get('app_id')))

        self.publish('ack', {})
        self._status_led.off()

    def publish(self, subtopic: str, payload: dict):
        # TODO: retain/qos
        topic = '{}/{}'.format(
            self._base_publish_topic,
            subtopic.strip('/')
        )
        print('CORE: publish {} {}'.format(topic, payload))
        self._mqtt.publish(topic.encode(), json.dumps(payload), qos=0) # TODO: qos=1 wants wait_message

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            f.write(json.dumps(self._config))

    def __del__(self):
        self._wlan.__del__()
