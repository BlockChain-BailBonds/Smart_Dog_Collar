# Smart Collar — bench acceptance and evidence ledger

Use this as a reproducible checklist, NOT a certificate of product safety. Every unmeasured line is **UNVERIFIED**.

## Automated (can run without electronics)

~~~bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
pio run -e esp32-s3-devkitc-1
~~~

Expected: offline Python unit tests pass and the PlatformIO firmware **compiles**. These tests use synthetic waveforms and do not demonstrate bark classification, volume safety or correct GPIO wiring.

## Physical bench gates — fill in results before animal fitting

| Gate | Procedure and pass criteria | Result / evidence |
| --- | --- | --- |
| Power rails | Measure voltage at mic, MPU, amp and S3; within component tolerances at audio/RF load; no backfeed | UNVERIFIED |
| Battery protection | Validate short/overcurrent/under-voltage/thermal protections; charge off-animal | UNVERIFIED |
| Microphone I2S | Capture quiet versus controlled acoustic stimulus; finite RMS telemetry; no obvious overrun | UNVERIFIED |
| Accelerometer | Verify I2C device and direction-dependent changes, no I2C lockups | UNVERIFIED |
| PCM and amp | Verify correct phrase, no clipping or I2S stalls, speaker wiring isolated from GND | UNVERIFIED |
| Acoustic exposure | Measure worst-case collar proximity to ears; independent expert approval for animal use | UNVERIFIED |
| Self-trigger | Play all prompts with mic active; no persistent feedback loops | UNVERIFIED |
| Temperature | Measure MCU, power-path, battery and enclosure under sustained load; no unsafe hot spots | UNVERIFIED |
| Battery life | Record actual run time and idle/audio current; no inferred 3500 mAh duration | UNVERIFIED |
| BLE privacy | With BLE ON, verify event-only short frames; no audio, no secret data; evaluate security separately | UNVERIFIED |
| Accuracy | Record event precision/recall and false alerts/hour in representative real environments | UNVERIFIED |
| Classifier | Per-class F1/confusion matrix using separate days, dogs and sessions; confidence calibration | UNVERIFIED |
| Wear safety | Qualified review of enclosure, breakaway collar, chew/ingress/impact, skin pressure and entanglement | UNVERIFIED |

## Measurement log schema

Retain a private measurement log with fields: date, device hardware revision, firmware Git SHA, test operator, test location (private), instrument make/calibration, ambient conditions, measurement units, numerical measurements, accepted limit/source, pass/fail, and raw evidence file reference. Do not put owner identity, location history or animal medical data in public Git.

## Distinguish verified from hypothesized

- VERIFIED IN CI only: software syntax/build and deterministic synthetic tests after successful workflow completion.
- NOT VERIFIED: enclosure, electronics, physical GPIO wiring, battery, safety, GPS/biometrics, barking intent and emotional interpretation.
- NOT IMPLIED: passing GitHub Actions means ready to wear or a faithful translation of animal vocalizations.

See [SAFETY.md](SAFETY.md), [AI_AND_DATA.md](AI_AND_DATA.md), and [COMPLETE_SETUP.md](COMPLETE_SETUP.md).
