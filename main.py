while True:
    try:
        # 'c' is available from boot.py
        c.start()
    except OSError:
        pass


