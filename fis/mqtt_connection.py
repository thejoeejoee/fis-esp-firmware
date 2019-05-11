from .mqtt_as import MQTTClient as BaseMQTTClient
from .mqtt_as import esp32_pause, asyncio, ticks_diff, ticks_ms, gc
from micropython import const

_DEFAULT_MS = const(20)

gc.collect()

class MQTTConnection(BaseMQTTClient):
    MAX_ATTEMPTS = 3

    def __init__(self, status_led, wifi_creds=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._creds = wifi_creds
        self._status_led = status_led

    async def _status_led_controller(self):
        """Notifier about wifi status - led is blinking in case of disconnected wifi."""
        while True:
            if not self.isconnected():
                self._status_led.on()
                await asyncio.sleep(.5)
                self._status_led.off()
                await asyncio.sleep(.5)
            else:
                await asyncio.sleep(5)

    async def wifi_connect(self):
        """
        Custom reimplementation of wifi connection - differences:
        - support only for ESP32
        - support for multiple wlan credentials
        - at first call starts wifi notifier
        """
        if not self._has_connected:
            loop = asyncio.get_event_loop()
            loop.create_task(self._status_led_controller())  # User handler.

        s = self._sta_if

        cred_index = 0

        while True:
            s.disconnect()
            esp32_pause()  # Otherwise sometimes fails to reconnect and hangs
            await asyncio.sleep(1)

            ssid, pw = self._creds[cred_index]
            self.dprint('Connecting to {}.'.format(ssid))
            s.connect(ssid, pw)

            attempt = 0
            self.dprint('Is connected at attempt {}? {}'.format(attempt, s.isconnected()))

            for i in range(7):
                esp32_pause()
                await asyncio.sleep(1)
                if s.isconnected():
                    break

            self.dprint('Is connected at final attempt {}? {}'.format(attempt, s.isconnected()))
            if s.isconnected():
                break
            cred_index = (cred_index + 1) % len(self._creds)

        current = self._creds[cred_index]
        self.dprint('Connected to {} ({})!'.format(current[0], '; '.join(s.ifconfig())))
        # insert working WLAN as first
        self._creds.remove(current)
        self._creds.insert(0, current)

        # Ensure connection stays up for a few secs.
        self.dprint('Checking WiFi integrity.')
        t = ticks_ms()
        while ticks_diff(ticks_ms(), t) < 5000:
            if not s.isconnected():
                raise OSError('WiFi connection fail.')  # in 1st 5 secs
            esp32_pause()
            await asyncio.sleep(1)

        self.dprint('Got reliable connection')
        # Timed out: assumed reliable

    async def _handle_msg(self):
        try:
            while self.isconnected():
                async with self.lock:
                    gc.collect()
                    await self.wait_msg()  # Immediate return if no message
                await asyncio.sleep_ms(_DEFAULT_MS)  # Let other tasks get lock

        except OSError:
            pass
        self._reconnect()  # Broker or WiFi fail.

    def dprint(self, *msg):
        # if self.DEBUG:
        print('MQTT: {}'.format(' '.join(map(str, msg))))
