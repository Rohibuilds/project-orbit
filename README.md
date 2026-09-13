<div align="center">

# Project ORBIT

**Modular desk assistant combining computer vision, voice interaction and practical electronics tools.**

![Status](https://img.shields.io/badge/status-active_development-5D6BFF?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Modular_AI_system-101820?style=flat-square)
![Brand](https://img.shields.io/badge/by-RA_TECH-101820?style=flat-square)

</div>

## Overview

Project ORBIT is a modular desk assistant designed to bring vision, voice, and practical electronics tools into one workspace. The planned system reuses a compact laptop mainboard and display while adding a desk camera and an articulated assistant arm.

> **Project status:** Active development

## Highlights

- Voice-based desk assistance
- Camera-assisted component inspection
- Resistor identification workflow
- Modular hardware architecture
- Repurposed laptop mainboard and display
- Expandable robotic desk-arm concept

## Hardware

| Component | Role |
|---|---|
| Samsung laptop mainboard with 8 GB DDR3 | Main processing and control |
| SSD storage | Project subsystem |
| Wi-Fi and Bluetooth | Project subsystem |
| 12-inch LCD | Project subsystem |
| Desk camera | Project subsystem |
| Arm actuators and controller electronics | Project subsystem |

## Repository structure

```text
project-orbit/
├── firmware/   Tested source code and configuration notes
├── hardware/   Wiring, components, PCB, and enclosure information
├── docs/       Build guide, calibration, results, and troubleshooting
├── media/      Prototype images, diagrams, and demo links
└── README.md   Project overview and release status
```

## Current public release

This initial release establishes the verified project overview and a clean documentation structure. Firmware, wiring diagrams, and media will be added only after each item is checked for accuracy and private credentials are removed.

## Roadmap

- [ ] Finalize the mechanical arm architecture
- [ ] Integrate the desk camera
- [ ] Build the resistor-recognition pipeline
- [ ] Add the voice interface
- [ ] Publish tested modules as separate releases

## Safety and reproducibility

- Verify every supply voltage before powering the controller or modules.
- Use a common ground and a power source sized for peak motor or audio current.
- Never commit Wi-Fi passwords, API keys, personal contact details, or certificates.
- Recheck the published pin map against the tested hardware before assembly.

---

<div align="center">

**Designed and developed by [Rohi · RA TECH](https://github.com/Rohibuilds)**

<sub>Build. Test. Improve. Share.</sub>

</div>
