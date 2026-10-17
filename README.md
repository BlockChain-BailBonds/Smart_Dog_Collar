# 918 Technologies · Smart Dog Collar Translator

Open-source reference design for a **smart talking dog collar** that detects bark-like sounds, reads movement context, and plays owner-configured words through a speaker on the collar.

**Status: development reference, not a validated finished wearable.** The repository supplies wiring, firmware, audio asset generation, an optional individually trained model workflow, a local BLE companion page, setup/testing instructions, and a safety checklist. Hardware assembly, enclosure fit, battery runtime, model quality, and animal-welfare testing have **not** been independently verified.

## Capabilities and evidence

| Capability | Included | Limitation |
| --- | --- | --- |
| On-device I2S microphone capture | Yes | Pin assignments must be checked on the actual ESP32-S3 carrier |
| Bark-like loud-sound event detection | Yes | Energy threshold is a baseline; non-barks can trigger |
| MPU6050 movement context | Yes | It is not a heart-rate or emotional-state measurement |
| Spoken words on **collar speaker** | Yes, after generating and flashing PCM assets | Playback is rule-selected or owner-labeled, not literal animal translation |
| Per-dog supervised classifier | Train/export pipeline included | No weights shipped: owners must collect and label dog-specific audio |
| BLE notifications / companion browser page | Optional, disabled by default | Browser requires supported Web Bluetooth over HTTPS; not an authenticated medical/remote-control system |
| MAX86150 optical/ECG biometrics | Concept only | Fur/contact and skin-electrode constraints; **not integrated** |
| GPS | Concept only | No GPS receiver driver or geofencing implemented |
| Production board / enclosure / battery certification | No | Validate these separately before any on-animal use |

### Reference bill of materials

- ESP32-S3 development carrier (example: ESP32-S3-DevKitC-1); earlier compact-module concept: ESP32-S3-MINI.
- INMP441 **I2S** microphone, 3.3 V breakout.
- MAX98357A **I2S** amplifier, 3.3 V supply, 8 Ω 1 W speaker (earlier COM-10988 speaker concept).
- MPU6050 accelerometer/gyroscope breakout (3.3 V-compatible).
- Protected single-cell Li-ion battery, matched 1-cell charger/protection module, and appropriately rated **regulated** 3.3 V buck-boost rail. Earlier proposals also included an 18650 3500 mAh cell and TP4056 charger; **TP4056 alone does not implement the complete battery power system**.
- Switch, wiring, strain relief, sealed **non-airtight** electronics housing, collar safety release, acoustic outlet, and mechanical mounting hardware.
- Optional research-only: MAX86150 biometric module and GPS receiver. Earlier alternative audio platform: ESP32-LyraT (not the target of this firmware).

Start with [complete setup](docs/COMPLETE_SETUP.md), [wiring/power](docs/HARDWARE.md), [setup/flash](docs/SETUP.md), [validation checklist](docs/VALIDATION.md), [machine-readable hardware manifest](config/hardware_reference.json), [AI/data](docs/AI_AND_DATA.md), and [safety](docs/SAFETY.md).

## System flow

1. INMP441 streams 16 kHz signed audio samples into ESP32-S3 I2S0.
2. Firmware computes RMS/zero-crossing/crest features from a short window, plus MPU6050 acceleration deviation.
3. Loud windows cause a **bark-like event**. Optional user-trained decision tree maps features to owner-defined observational labels; low-confidence predictions are marked uncertain.
4. MAX98357A on I2S1 plays a locally stored 22,050 Hz PCM spoken phrase. Untrained mode says “I am barking.”
5. USB serial emits event and once-per-second calibration telemetry as JSON; optional BLE sends compact B|label notifications only, never continuous audio by default.

**Do not claim to decode what a dog is thinking.** Bark context/intent labels are hypotheses based on owner observation, not verified language or clinical diagnoses.

## Quick start (bench only)

~~~bash
python -m pip install platformio
# Ubuntu / Debian / Termux proot:
sudo apt-get install espeak
python scripts/build_audio.py
pio run
# Connect USB, then:
pio run -t upload
pio run -t uploadfs
pio device monitor -b 115200
~~~

The audio generator needs the local command named "espeak". For Windows, install a compatible command-line eSpeak binary. Review the GPIO and power table **before flashing**. To set microphone noise threshold, edit BARK_RMS_THRESHOLD in src/main.cpp; collect serial data in a quiet room, then introduce controlled bark samples. The defaults are initial engineering values, not pre-calibrated accuracy.

## Repository map

| Path | Purpose |
| --- | --- |
| src/main.cpp | ESP32-S3 on-device sensing, safe default event flow, PCM speaker and opt-in BLE |
| include/model_enabled.h | Deliberately **untrained** default decision-tree model |
| scripts/build_audio.py | Creates on-collar spoken PCM assets from local speech synthesis |
| scripts/train_model.py | Owner-labeled WAV -> decision-tree header, group-heldout evaluation |
| examples/dataset_index.csv | Input CSV schema (no personal recordings in repo) |
| web/index.html | Optional Android Chrome Web Bluetooth event view |
| docs/ | Wiring, installation, data/AI and dog safety |
| .github/workflows/ci.yml | Python syntax, synthetic data tests, manifest checks and PlatformIO firmware build on GitHub |
| config/hardware_reference.json | Hardware, I/O pins, protocols and unverified feature status in machine-readable form |
| tests/ | Offline deterministic synthetic-data and exported-model validation |
| docs/VALIDATION.md | Reproducible bench acceptance checklist and measurement record |
| docs/CHANGELOG.md | Dated change history and feature verification status |

## Validation and nonclaims

The GitHub workflow compiles the target firmware and exercises synthetic dataset/model-export checks; hardware, battery, speaker, sensors and animal behavior remain **unverified** until measured. For full test commands and pass/fail gates, see [VALIDATION.md](docs/VALIDATION.md). Training input recordings are never uploaded by the provided firmware or CI workflow.

## Prior design evolution

Initial 2025 design named an ESP32-LyraT audio platform with INMP441, MAX86150, MPU6050, MAX98357A and a LiPo/TP4056 concept. A subsequent compact concept listed ESP32-S3-MINI, a microphone specified as “MPU6605Q,” COM-10988 speaker, 18650 and optional GPS. “MPU6605Q” is not treated here as a verified microphone model: the **explicit, known I2S part is INMP441**. The two proposed processor choices are alternatives, not interchangeable drop-in firmware targets.

## License and contribution

MIT — see LICENSE. Please contribute reproducible benchmarks, carrier-specific pinouts, acoustic tests, power measurements and evidence. Do not commit pet-identifying metadata, raw recordings without consent, credentials or location logs.

**918 Technologies · Smart_Dog_Collar**