# default port with connected ESP
PORT ?= /dev/ttyUSB0

MPY_CROSS ?= python -m mpy_cross

# used broker for remote deploy
BROKER_URL ?= fis.josefkolar.cz
BROKER_USERNAME ?= fis-esp-firmware-deploy
BROKER_PASSWORD ?= kqv5RS9LJ6RLY2eZ

# supported micropython
MICROPYTHON_BINARY_URL = http://micropython.org/resources/firmware/esp32-20180511-v1.9.4.bin
MICROPYTHON_BINARY = esp-micropython.bin

PYTHON_FILE_DUMPER="F=__import__('sys').argv[1];print(__import__('json').dumps(dict(file=F,content=open(F).read())))"
#PYTHON_FILE_DUMPER="B=__import__('base64');\
#F=__import__('sys').argv[1];\
#print(__import__('json').dumps(dict(file=F,content=B.b64encode(open(F, 'rb').read()))))\
#"


AMPY_DELAY = 0.5

AMPY := ampy -p $(PORT) -d $(AMPY_DELAY)

install: ## Perform installation proccess on purely new ESP32 (uPython+libs+fis+bootloader).
	make flash-micropython
	make install-libs
	make install-fis
	make console-with-reset

flash-micropython: erase-flash $(MICROPYTHON_BINARY) ## Flash micropython to connected ESP32.
	esptool.py --chip esp32 --port $(PORT) --baud 460800 write_flash -z 0x1000 $(MICROPYTHON_BINARY)

$(MICROPYTHON_BINARY): ## Downloads micropython binary.
	wget $(MICROPYTHON_BINARY_URL) -O $(MICROPYTHON_BINARY)

erase-flash: ## Erase entire flash on connected ESP32.
	esptool.py --chip esp32 --port $(PORT) erase_flash

put-config: ## Put config.json to ESP32.
	make reset-chip
	$(AMPY) put config.json

put-install: ## Put _install.py (first start install script) to ESP32.
	make reset-chip
	$(AMPY) put _install.py

install-libs: put-config put-install ## Install required libs (via install script) on connected ESP32.
	make reset-chip
	$(AMPY) run _install.py

install-fis: disable-autoloader ## Install FIS package with fis-bootloader on to ESP32.
	make reset-chip
	$(AMPY) rmdir fis || true
	make reset-chip
	# find fis -type f | xargs -n 1 $(AMPY) put
	$(AMPY) put fis/ fis
	make reset-chip
	$(AMPY) rm boot.py || true
	make reset-chip
	$(AMPY) put boot.py

enable-autoloader: ## Enable FIS autoloader on ESP32.
	make reset-chip
	$(AMPY) put main.py

disable-autoloader: ## Disable FIS autoloader on ESP32.
	make reset-chip
	$(AMPY) rm main.py || true

console-with-reset: ## Run console after ESP32 reset.
	make reset-chip
	make console

console: ## Run console without reset.
	picocom $(PORT) -b115200

reset-chip: ## Reset connected chip.
	esptool.py --chip esp32 --port $(PORT) --after hard_reset read_mac && sleep 2

remote-deploy: ## Based on given NODE_ID performs remote deploy (from actual fis/, so be careful) via broker to target.
	test -n $(NODE_ID) || echo Missing NODE_ID! || exit 2;
	# find fis -type f -regex ".*\.py" |\
	# xargs -n1 -IFILE sh -c "python -m mpy_cross FILE && echo FILE | sed s/.py/.mpy/" |\
	find fis -type f -regex ".*\.py" |\
	 xargs -n 1 python -c $(PYTHON_FILE_DUMPER) |\
	 mosquitto_pub -q 1 -u $(BROKER_USERNAME) -P $(BROKER_PASSWORD) -h $(BROKER_URL) -t fis/to/$(NODE_ID)/app/config -l

remote-reset: ## Based on given NODE_ID performs remote reset - IF IS NOT ENABLED AUTOLOADER, NODE FREEZES AFTER RESET.
	test -n $(NODE_ID) || echo Missing NODE_ID! || exit 2;
	python -c "print(__import__('json').dumps(dict(payload=dict(action='reset'))))" |\
	 mosquitto_pub -q 1 -u $(BROKER_USERNAME) -P $(BROKER_PASSWORD) -h $(BROKER_URL) -t fis/to/$(NODE_ID)/app/config -l

help: ## Display available commands with description.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'