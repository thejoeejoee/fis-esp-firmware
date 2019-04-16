import machine

try:
    # 'c' is available from boot.py
    c.start()
except Exception as e:
    machine.reset()


