# coding=utf-8
import esp
import micropython

micropython.alloc_emergency_exception_buf(128)
esp.osdebug(None)

from .wlan import WLAN
import json

from umqtt.robust import MQTTClient

import time
import machine
import binascii
import neopixel

CONFIG_FILE = 'config.json'


class Core:
    def __init__(self):
        with open(CONFIG_FILE) as f:
            self._config = json.loads(f.read())

        self._wlan = WLAN(self._config.get('wlans'))
        self._adc = machine.ADC(machine.Pin(34))
        self._adc.atten(self._adc.ATTN_11DB)  # 150 to 1750mV

        self._id = binascii.hexlify(machine.unique_id())
        self._mqtt = MQTTClient(self._id, "fis.josefkolar.cz")  # TODO: to config
        self._mqtt.DEBUG = True

        self._status_led = machine.Signal(machine.Pin(2, machine.Pin.OUT))
        self._neopixel = neopixel.NeoPixel(machine.Pin(4, machine.Pin.OUT), 10)

    def start(self):
        self._wlan.connect()

        while not self._wlan.is_connected:
            self._status_led.on()
            time.sleep_ms(100)
            self._status_led.off()
            time.sleep_ms(100)

        self._mqtt.connect(clean_session=False)
        self._mqtt.set_callback(self._on_message)

        topic = '/node/{}'.format(self._id.decode())
        self._mqtt.subscribe(topic.encode())
        print('CORE: subscribed to {}.'.format(topic))

        while True:
            v = self._adc.read()

            self._mqtt.wait_msg()

    def _on_message(self, topic, message):
        self._status_led.on()
        command = json.loads(message)

        print('CORE: message {}, {}'.format(topic, message))

        if command.get('app') == 'neopixel':
            self._neopixel.fill((command.get('data').get('brightness'),) * 3)
            self._neopixel.write()

        self._mqtt.publish(b'/ack', json.dumps(dict(node=self._id)))

        time.sleep_ms(50)
        self._status_led.off()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            f.write(json.dumps(self._config))

    def __del__(self):
        self._wlan.__del__()
