# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
import binascii

import network
import json
import time
import upip
import machine

MAX_ATTEMPTS = 3

status = machine.Signal(machine.Pin(2, machine.Pin.OUT))

wlans = json.load(open('./config.json')).get('wlans')

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

wlan_i = 0
while True:
    attempt = 0
    print('Attempt to connect to {}.'.format(wlans[wlan_i][0]))
    sta_if.connect(*wlans[wlan_i])  # Connect to an AP

    while not sta_if.isconnected() and attempt <= MAX_ATTEMPTS:
        status.on()
        time.sleep(1)
        status.off()
        time.sleep(1)
        attempt += 1

    if sta_if.isconnected():
        break

    wlan_i = (wlan_i + 1) % len(wlans)

print('Connected!')

upip.install('micropython-uasyncio')

print('\nInstallation SUCCESSFUL! fis-node ID: {}\n'.format(binascii.hexlify(machine.unique_id()).decode()))
