# Project ORBIT
**Rohi | RA TECH** · AI workbench assistant

ORBIT runs on the recovered PC/laptop computing platform and combines a desk camera, project memory, photo/video capture, experimental resistor recognition and optional voice/local AI.

**[Open the main Python code](orbit.py) · [Modules](modules) · [Hardware](hardware/README.md) · [How to build](docs/README.md)**

## Included source
- `orbit.py`: Flask dashboard, command handling, camera and voice loops.
- `modules/`: capture, speech, local AI, project storage and resistor decoding.
- `config.json`, `requirements.txt`, `install.sh`: setup and configuration.
- `tests/`: storage, decoding, API and camera-failure regression checks.

Recovered from **ORBIT_v1_Source_Code.zip** and **ORBIT_v1_Complete_Build_Guide.pdf**. This is the existing workstation software, not ESP32 firmware. Motorized-arm control is not present in the recovered source.

## Quick start on Ubuntu
```bash
bash install.sh
source .venv/bin/activate
python orbit.py
```
Read [the build guide](docs/README.md) before installation. Open **http://127.0.0.1:8080**. The dashboard binds to the local PC by default; the guide explains trusted-LAN phone access.

## Repairs
Atomic, thread-safe project storage; unique capture names; recording cleanup when a project ends; handling failed image/video writes; serialized commands; optional audio that fails gracefully; validation of API input; correct gold/silver resistor multipliers; portable dashboard element access; quoted installer paths.

[Validation record](docs/VALIDATION.md) · [Live automated test results](https://github.com/Rohibuilds/project-orbit/actions)
