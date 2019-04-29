import network
import json
import time
import upip

wlan = json.load(open('./config.json')).get('wlans')[0]

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.scan()  # Scan for available access points
sta_if.connect(*wlan)  # Connect to an AP
while not sta_if.isconnected():
    time.sleep(1)

print('Connected!')

upip.install('micropython-uasyncio')