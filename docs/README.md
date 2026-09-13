# Build and use ORBIT v1
1. Assemble and test the computer, SSD, cooling, display, USB camera, microphone and speaker. Install Ubuntu and verify each device in the OS first.
2. Download the whole repository and extract it into a user-owned folder. In a terminal there, run `bash install.sh`. The script installs system dependencies, creates `.venv`, installs Python packages and adds a desktop-session autostart entry. It uses `sudo` for package installation.
3. Edit `config.json`: camera index, capture dimensions, frame rate, project folder and user name. Project files remain local under the configured folder and are ignored by git.
4. Run `source .venv/bin/activate`, then `python orbit.py`. Open **http://127.0.0.1:8080**. Camera/audio absence is reported; typed commands remain usable when voice is unavailable.
5. For phone access, set `web_host` to `0.0.0.0`, restart ORBIT and use `http://COMPUTER_LAN_IP:8080` on the same trusted Wi-Fi. This prototype has no user authentication; do not expose or port-forward it to the internet or an untrusted network. Its camera feed and controls become reachable on that LAN.
6. For optional local AI, install Ollama using its [official instructions](https://github.com/ollama/ollama), start its local server, and run `ollama pull qwen2.5:0.5b`. Keep `ollama_model` aligned with the model installed. Camera/project commands do not require the AI server.
7. Use the controls below. Voice commands use a configured wake phrase such as **hey orbit**; speech recognition sends captured speech to the recognizer's online service. The local Ollama answer backend is separate.

| Command | Result |
|---|---|
| `start project LED Driver` | Create a uniquely named project folder |
| `take photo` | Save a camera image inside the current project |
| `start recording` | Start MP4 capture after confirming encoder availability |
| `stop recording` | Close and save the video |
| `identify resistor` | Inspect one horizontal four-band axial resistor |
| `remember use a 220 ohm resistor` | Save a project note |
| `end project` | Close recording and save the session |
| Other question | Ask the configured local AI backend |

## Resistor recognition
Place one four-band resistor horizontally inside the guide box, under neutral white light and in focus. Recognition is experimental and sensitive to lighting/body color; verify the result with a meter. Five/six-band decoding and automatic component classification are not implemented in this v1 source.

## Troubleshooting
- **Camera unavailable:** check the USB connection, camera index and whether another application owns it. Test `v4l2-ctl --list-devices` on Ubuntu.
- **No voice:** check the OS default input/output and microphone permissions. The installer includes PortAudio and eSpeak support; use typed commands while resolving audio issues.
- **Recording cannot start:** check the output folder's write access and MP4 codec. Failed starts are now reported rather than shown as active.
- **AI unavailable:** start Ollama and install the configured model. Core project controls still work.
- **Phone cannot connect:** check `web_host`, restart, verify both devices share the network and check the OS firewall.
- **Autostart unwanted:** remove `~/.config/autostart/orbit.desktop`; manual launch continues to work.

## Tests
```bash
python -m unittest discover -s tests -v
```
API tests use `ORBIT_HEADLESS=1` and temporary project storage. They test camera failure handling with controlled inputs, not physical camera/audio quality. The CI workflow installs its explicit test dependency versions and runs all tests.
