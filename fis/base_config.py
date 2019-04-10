from binascii import hexlify

config = {
    'client_id': hexlify(unique_id()),
    'server': None,
    'port': 0,
    'user': '',
    'password': '',
    'keepalive': 60,
    'ping_interval': 0,
    'ssl': False,
    'ssl_params': {},
    'response_time': 10,
    'clean_init': True,
    'clean': True,
    'max_repubs': 4,
    'will': None,
    'subs_cb': lambda *_: None,
    'wifi_coro': lambda *_: None,
    'connect_coro': lambda *_: None,
    'ssid': None,
    'wifi_pw': None,
}