from fis.core import Core

c = Core()
while True:
    try:
        c.start()
    except OSError:
        pass


