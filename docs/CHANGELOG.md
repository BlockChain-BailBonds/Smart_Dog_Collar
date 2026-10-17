# Change log

## 2026-10-17

- Published initial complete ESP32-S3 smart dog collar reference firmware, INMP441 microphone, MPU6050 motion sensing, MAX98357A PCM playback, optional BLE, offline phrase generation, optional owner-labeled ML training, wiring, build and animal safety notes.
- Hardened classifier export C++ floating literals and per-recording held-out split; reduced speaker digital amplitude; made BLE event frame intentionally compact to fit default ATT notification size.
- Consolidated complete bench assembly and configuration in docs/COMPLETE_SETUP.md and config/hardware_reference.json.
- Added once-per-second JSON serial signal telemetry for calibration and standardized hardware validation/evidence checklist.
- Fixed documented BLE wire format to B|label and added deterministic synthetic-data, pin-mapping and exported-header tests to CI.

Status: software build passing before latest changes; hardware and animal trials unverified. Do not interpret commits as certified performance.
