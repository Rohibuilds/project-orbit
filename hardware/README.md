# Hardware connections
The recovered ORBIT v1 build uses a PC/laptop motherboard, compatible RAM and boot SSD, its correctly rated power adapter/cooling, a display with the matching controller/interface, USB camera, USB microphone and USB or powered audio output.

| Device | Connection |
|---|---|
| Boot SSD | Compatible motherboard storage connector |
| Display | Motherboard video output through its matching display/controller path |
| Desk camera | USB |
| Microphone | USB / selected OS input device |
| Speaker | USB or the computer's audio output to a powered speaker |
| Phone dashboard | Same trusted local network, after enabling LAN binding |

ORBIT v1 does not define ESP32 GPIO wiring or drive a robotic arm. Use the original motherboard's supported supply and cooling. A bare laptop LCD requires a controller specifically compatible with its panel; the Python software cannot substitute for that electrical interface.
