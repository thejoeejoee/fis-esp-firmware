# coding=utf-8

import machine
import network


class WLAN:
    WLAN_TIMEOUT = 2 * 1000
    WLAN_TRIES_LIMIT = 3

    def __init__(self, wlans: list):
        self._wlan = network.WLAN(network.STA_IF)
        self._timer = machine.Timer(-1)
        self._credential_index = self._tries = 0
        self._is_connected = False

        self._wlans = wlans

    def connect(self):
        self._wlan.active(True)
        self._wlan.scan()
        self._timer.init(
            period=self.WLAN_TIMEOUT,
            mode=machine.Timer.PERIODIC,
            callback=self._connect
        )
        self._connect()

    def _connect(self, timer=None):
        if self._wlan.isconnected():
            if not self._is_connected:
                current = self._wlans[self._credential_index]
                print('WLAN: Connected to {} ({})!'.format(
                    current[0],
                    '; '.join(self._wlan.ifconfig())
                ))
                # insert working WLAN as first
                self._wlans.remove(current)
                self._wlans.insert(0, current)
            self._is_connected = True
            return

        self._is_connected = False
        if self._tries >= self.WLAN_TRIES_LIMIT:
            self._credential_index = self._credential_index + 1 if self._credential_index + 1 < len(self._wlans) else 0
            print('WLAN: trying next AP: {}.'.format(self._wlans[self._credential_index][0]))
            self._tries = 0
        elif self._tries == 0:
            ssid, password = self._wlans[self._credential_index]
            self._wlan.connect(ssid, password)
            print('WLAN: connecting to {}.'.format(ssid))
            self._tries += 1
        else:
            self._tries += 1
            print('WLAN: waiting for connection to {} ({}/{}).'.format(
                self._wlans[self._credential_index][0],
                self._tries,
                self.WLAN_TRIES_LIMIT
            ))

    @property
    def is_connected(self):
        return self._is_connected

    def __del__(self):
        self._wlan.active(False)
        self._timer.deinit()


__all__ = ['WLAN']

