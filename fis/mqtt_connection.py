from .mqtt_as import MQTTClient as BaseMQTTClient
from .mqtt_as import esp32_pause, asyncio, ticks_diff, ticks_ms


class MQTTConnection(BaseMQTTClient):
    MAX_ATTEMPTS = 3

    def __init__(self, status_led, wifi_creds=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._creds = wifi_creds
        self._status_led = status_led

    async def wifi_connect(self):
        s = self._sta_if

        s.disconnect()
        esp32_pause()  # Otherwise sometimes fails to reconnect and hangs
        await asyncio.sleep(1)
        cred_index = 0

        while True:
            ssid, pw = self._creds[cred_index]
            self.dprint('Connecting to {}.'.format(ssid))
            s.connect(ssid, pw)

            attempt = 0
            while not s.isconnected() and attempt <= self.MAX_ATTEMPTS:
                # ESP32 does not yet support STAT_CONNECTING
                esp32_pause()
                # https://github.com/micropython/micropython-esp32/issues/167 still seems necessary
                await asyncio.sleep(1)
                attempt += 1

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

    def dprint(self, *msg):
        # if self.DEBUG:
        print('MQTT: {}'.format(' '.join(map(str, msg))))
