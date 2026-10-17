# Build, flash, calibration and companion app

## Prerequisites

A working ESP32-S3 reference development board, USB data cable, compatible 3.3 V peripheral power, INMP441, MAX98357A, 8 Ω speaker and MPU6050; Python 3, PlatformIO, and the eSpeak executable for local phrase generation.

~~~bash
git clone https://github.com/BlockChain-BailBonds/Smart_Dog_Collar.git
cd Smart_Dog_Collar
python -m pip install platformio
python scripts/build_audio.py
pio run
pio run -t upload
pio run -t uploadfs
pio device monitor -b 115200
~~~

Adjust your actual serial port by adding -p PORT to pio device monitor, and upload_port in platformio.ini if automatic port discovery fails. Use appropriate USB permissions in Linux/Termux/Android; no USB path is hardcoded.

**Do not run an S3-MINI bare module from this DevKitC pinout without checking its carrier.**

## Expected serial output

At boot firmware prints four status bits for microphone, amp, MPU6050 and LittleFS, plus whether a user-trained model is included. Loud audio yields one JSON line with event=bark_like, label=untrained, signal features, and optional acceleration context. A healthy MCU boot is not proof of correct mic capture or bark-specific accuracy.

Once per second the device also prints serial JSON with event=telemetry and numerical rms, zcr, crest and motion_g values for bench-only threshold calibration (no raw recordings). The default RMS threshold 750 is a **starting value**, not experimentally validated. Compare quiet and target-bark RMS, then set a value above ambient with headroom. Default cooldown is 2.5 s; output suppression avoids the speaker retriggering itself. These settings can suppress closely spaced barks.

## Spoken phrases

Audio is generated with a local/offline eSpeak engine and written as PCM into data/. The firmware expects 22,050 Hz signed 16-bit little-endian **raw** mono:
- bark.pcm: “I am barking.”
- alert.pcm: “I might be alerting you.”
- attention.pcm: “I might want attention.”
- play.pcm: “I might want to play.”

Modify DEFAULT_PHRASES in scripts/build_audio.py and rerun the generator + uploadfs to change language or words. eSpeak voice support varies by installation; verify exact pronunciation, language, level and phrase duration away from the animal. Missing assets are logged and never silently synthesized in cloud services.

## Optional BLE / Android browser

Change the flag in platformio.ini from -D ENABLE_BLE=0 to -D ENABLE_BLE=1; rebuild and flash. This starts unencrypted, event-only BLE advertising, with service UUID 9f4b3200-9e08-4ad1-bdc1-f98c8617ac01 and notify characteristic ending ac02. It sends compact notifications of the form B|bark, B|alert, B|attention, or B|play (a maximum of 11 bytes), **not serial JSON or raw audio**. Serial remains newline-delimited JSON. No bond management/authentication is implemented; keep it off outside a controlled test environment.

The optional web/index.html uses browser Web Bluetooth. Serve it via HTTPS (e.g. a properly configured Pages origin) or localhost with a compatible Bluetooth-enabled browser, generally Chrome on Android. Browser requirements and device permissions vary. Click Connect from a direct user gesture; enable phone TTS only if the owner explicitly opts in. The collar itself plays PCM independently.

## Recording dataset and optional model

Keep all recordings in a private local directory, not Git. Each example WAV must be 16 kHz mono PCM16; index CSV columns are path,label,motion_g and paths are relative to that CSV.

~~~bash
python -m pip install numpy scikit-learn
python scripts/train_model.py --index private_dataset/index.csv
pio run
pio run -t upload
~~~

This produces include/model_enabled.h containing only decision-tree weights/thresholds; decide whether your training outcome is suitable to publish before committing generated weights. Training data (audio) stay local. Obtain repeated sessions and neutral/background examples before accepting performance claims. Read [AI_AND_DATA.md](AI_AND_DATA.md).

## Repeatable validation

Use the [complete setup](COMPLETE_SETUP.md), [hardware manifest](../config/hardware_reference.json), and [validation record](VALIDATION.md). Desktop synthetic-data tests are in tests/ and run on GitHub Actions. A successful build or synthetic-data test does not establish actual wearable safety or real-world bark accuracy.

## Debugging

- Silent microphone: check INMP441 L/R tied to ground, 3.3 V, SCK/WS, pin mapping, I2S channel.
- Mic constantly triggers: lower gain by reducing background noise or **raise RMS threshold** after measurement; test speaker echo.
- Silent speaker: check LittleFS status and uploadfs, 3.3 V, BCLK/LRC/DIN, speaker between SPK+ and SPK-, SD/gain configuration.
- Missing MPU6050: verify 0x68, AD0, I2C pullups, breakout levels, GPIOs.
- Failing builds: use the pinned PlatformIO environment; report exact compiler output; hardware builds are not verified merely from repository publication.
