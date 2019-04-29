PORT=/dev/ttyUSB0
MICROPYTHON_BINARY_URL=http://micropython.org/resources/firmware/esp32-20190125-v1.10.bin
MICROPYTHON_BINARY=esp-micropython.bin


install:
	make flash-micropython
	make install-libs
	make install-fis
	make console-with-reset

flash-micropython: erase-flash $(MICROPYTHON_BINARY)
	esptool.py --chip esp32 --port $(PORT) --baud 460800 write_flash -z 0x1000 $(MICROPYTHON_BINARY)

$(MICROPYTHON_BINARY):
	wget $(MICROPYTHON_BINARY_URL) -O $(MICROPYTHON_BINARY)

erase-flash:
	esptool.py --chip esp32 --port $(PORT) erase_flash

put-config:
	make reset-chip
	ampy -p $(PORT) put config.json
put-install:
	make reset-chip
	ampy -p $(PORT) put _install.py

install-libs: put-config put-install
	make reset-chip
	ampy -p $(PORT) run _install.py

install-fis:
	make reset-chip
	ampy -p $(PORT) put fis
	make reset-chip
	ampy -p $(PORT) put boot.py

enable-autoloader:
	make reset-chip
	ampy -p $(PORT) put main.py

console-with-reset:
	make reset-chip
	make console

console:
	picocom $(PORT) -b115200


reset-chip:
	esptool.py --chip esp32 --port $(PORT) --after hard_reset read_mac && sleep 2