# 918 Technologies Smart Talking Dog Collar — complete setup

Last consolidated: 2026-10-17. **Public reference implementation; bench only.** It is not a commercially manufactured or animal-validated device.

## 1. Scope and what is actually implemented

The ESP32-S3 DevKitC-1 reference firmware samples an INMP441 I2S microphone, measures motion through an MPU6050, and plays local owner-configured audio phrases through an I2S amplifier and small speaker. The detection gate uses a short-window RMS threshold, so claps, wind, other dogs and noise may be misclassified as bark-like events. A separately trained per-dog decision tree can categorize owner-observed context; no trained model is bundled. Optional unencrypted BLE broadcasts event labels but does not stream speech or microphone audio. **No dog-to-English translation is proven.**

## 2. Hardware reference set

| Item | Exact reference/role | Verified status |
| --- | --- | --- |
| Controller | ESP32-S3 DevKitC-1; 3.3 V GPIO | Firmware CI builds; physical carrier not tested |
| Microphone | INMP441 digital I2S, left channel selected | Driver included; physical connection unverified |
| Motion sensor | MPU6050 I2C, 0x68 | Driver included; calibration and hardware unverified |
| Speaker output | MAX98357A I2S amplifier and 8 Ω 1 W speaker | PCM driver and assets script included; acoustic levels unmeasured |
| Battery | Protected 1S Li-ion with engineered charger/protection and regulated 3.3 V | Proposed electrical architecture only |
| Optional clinical sensing | MAX86150 optical/ECG | NOT integrated or validated on fur |
| Optional location | GPS/GNSS hardware | NOT integrated; no geofencing |
| Compact board | ESP32-S3-MINI, ESP32-LyraT concept | NOT interchangeable with DevKitC-1 pinout or driver |

Earlier candidate parts included a 3500 mAh 18650, TP4056 and COM-10988 speaker. These are **candidates**, not validated assembly specifications. An item previously named MPU6605Q is not used as a verified microphone; this repo explicitly targets the INMP441. Do not substitute an analog mic without rewriting the audio interface.

## 3. Wiring — verify GPIO availability on your board before power

| Module | Signal -> S3 | Notes |
| --- | --- | --- |
| INMP441 | SCK=GPIO5; WS=GPIO4; SD=GPIO6; L/R=GND | 3.3 V only; shared GND |
| MAX98357A | BCLK=GPIO7; LRC=GPIO15; DIN=GPIO16 | 3.3 V rated supply and shared GND; SPK+ and SPK- go to speaker terminals |
| MPU6050 | SDA=GPIO8; SCL=GPIO9; AD0=GND | I2C at 100 kHz, address 0x68; check breakout level compatibility |

Regulated 3.3 V feeds microcontroller only through **the specific board's authorized 3V3 power entry**, microphone, amplifier and MPU6050. Do **not** feed external 3.3 V and USB simultaneously unless board-specific backfeed protections are confirmed. Do not wire a battery directly to the regulator output or to any GPIO. Reference JSON: [config/hardware_reference.json](../config/hardware_reference.json). Full risks in [HARDWARE.md](HARDWARE.md) and [SAFETY.md](SAFETY.md).

## 4. Install and bench-flash

Work from a desktop Linux PC or suitable Termux Ubuntu/proot environment with direct access to an ESP32-S3 USB device. USB access on Android depends on OS permissions and may require dedicated flashing arrangements. Do not assume that a proot USB path or device-port name is valid without inspection.

~~~bash
git clone https://github.com/BlockChain-BailBonds/Smart_Dog_Collar.git
cd Smart_Dog_Collar
python -m pip install platformio==6.1.18
# On Ubuntu/Debian install eSpeak separately with: sudo apt-get install espeak
python scripts/build_audio.py
pio run -e esp32-s3-devkitc-1
pio run -t upload
pio run -t uploadfs
pio device monitor -b 115200
~~~

On first boot watch the status line for mic, speaker, motion and LittleFS. The speaker requires an uploaded LittleFS image generated from data/*.pcm assets. No internet AI/translation service is required.

## 5. Calibrate using live serial observations

Firmware emits a telemetry JSON line about once per second with rms, zcr, crest, motion_g. On actual bark-like triggers it sends another event JSON with label and confidence. Record quiet-room, room-noise, movement and known-bark data with controlled conditions. Edit BARK_RMS_THRESHOLD in src/main.cpp only **after** observing these levels. Defaults: RMS 750, 2.5 s event cooldown, 0.8 s speaker self-trigger guard. Values are starting points, not tuned guarantees.

## 6. Speech and optional per-dog training

Run the offline eSpeak generator to create bark.pcm, alert.pcm, attention.pcm and play.pcm, which are reproduced from the collar, **not merely a phone**. Phrases explicitly express uncertainty. To classify observational contexts, privately gather at least 10 distinct WAV recordings, 16 kHz mono signed PCM16, with CSV path,label,motion_g. Install numpy and scikit-learn and run the supervised trainer. It exports include/model_enabled.h with a decision tree but cannot establish intent from audio. Distinct recordings are used for stratified train/test splitting; future-day holdout validation is still necessary.

~~~bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/train_model.py --index private_dataset/index.csv
pio run -t upload
~~~

Do not run the training command until you have your own dataset, and do not commit real recordings. All remote/synthetic CI tests operate on generated artificial waveforms.

## 7. BLE and phone companion

BLE remains OFF in platformio.ini. For a supervised lab session only, change ENABLE_BLE from 0 to 1 and reflash. The collar transmits a short string: B|bark, B|alert, B|attention or B|play. Bluetooth sends **no serial JSON and no raw microphone audio**. The local browser in web/index.html connects in a user gesture on compatible Chrome/Android in a secure context. Its optional phone speech is separate from on-collar speech. The reference BLE characteristic has no authentication, so **do not enable it for public use**.

## 8. Deployment and evidentiary status

Automated CI tests establish only compilation and deterministic synthetic-data behavior; they are not proof of electrical, acoustic, firmware-runtime, ML, enclosure or animal-welfare readiness. Required measured sign-offs are in [VALIDATION.md](VALIDATION.md). Until these pass, use a **bench mount, not an animal collar**. There are no production-certified PCB design files, custom enclosure measurements, runtime/battery curves, clinical vital signs or GPS demonstrations in this repository.
