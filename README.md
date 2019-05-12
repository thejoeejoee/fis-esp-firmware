# FIS ESP32 Firmware
ESP32 node firmware for Fast IoT Solution - easy home monitoring and automation with graphic setup.

Includes MicroPython firmware core with installation script, WiFi connection manager and basic applications.

`Makefile` supports:
```
console                        Run console without reset.
console-with-reset             Run console after ESP32 reset.
disable-autoloader             Disable FIS autoloader on ESP32.
enable-autoloader              Enable FIS autoloader on ESP32.
erase-flash                    Erase entire flash on connected ESP32.
flash-micropython              Flash micropython to connected ESP32.
help                           Display available commands with description.
install-fis                    Install FIS package with fis-bootloader on to ESP32.
install-libs                   Install required libs (via install script) on connected ESP32.
install                        Perform installation proccess on purely new ESP32 (uPython+libs+fis+bootloader).
put-config                     Put config.json to ESP32.
put-install                    Put _install.py (first start install script) to ESP32.
remote-reset                   Based on given NODE_ID performs remote reset - IF IS NOT ENABLED AUTOLOADER, NODE FREEZES AFTER RESET.
reset-chip                     Reset connected chip.
```



