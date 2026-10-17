# Supervised labels, inference limits, and measurement protocol

This project does **not** decode a canine language. A bark can convey different things in different contexts, and apparent emotion or intention cannot be recovered reliably from a few acoustic features alone. We implement explicit **owner-labeled observational categories**, not an animal's literal words.

## Defined categories

- alert — the owner observed behavior consistent with orienting/alerting
- attention — the owner observed seeking the handler's attention
- play — the owner observed a play interaction
- uncertain — unmatched context, neutral/noisy stimulus, and ambiguous examples

In an untrained build ALL detected bark-like events are "untrained" and the on-collar voice says “I am barking.” In a trained build, predictions below 0.70 confidence or class uncertain fall back to the neutral utterance.

## Data protocol

1. Collect **dog-specific**, consented 16 kHz mono PCM16 recordings in multiple places/days, as *distinct files*. Label only from directly observed context.
2. Keep ambiguous recordings as uncertain rather than guessing.
3. Record motion_g from a synchronized accelerometer snapshot if available; otherwise 0 and record that the sensor was absent.
4. Log how you defined the label and the source of potential background noise. Keep filenames and GPS/location/private names out of public repos.
5. Train a depth-limited decision tree on RMS, zero-crossing rate, crest factor and motion deviation. Export identical decision rules as a C++ header for on-device inference.
6. Hold out **recording files**, not just adjacent frames. The generated training script uses a stratified split of complete recordings.
7. Re-evaluate using entire future days, real-world ambient noise, other animals and the actual collar microphone. Provide confusion matrix, false positive rate per hour, latency and battery use before claiming deployment readiness.

The default trainer requires a minimum of 10 recordings and at least two recordings per class. That minimum is for software smoke testing, **not sufficient evidence of dog-intent accuracy**. Generated weights are not bundled; the reference detection uses an RMS gate which cannot reliably distinguish bark from other impulsive sounds.

## Metrics to report

- Event detector: precision, recall, false alerts/hour by scenario.
- Classifier: macro-F1, per-class precision/recall and test dog/session split; compare against majority-class baseline.
- Hardware: audio latency p50/p95, missed I2S frames, sample underflow, 3V3 droop, temperature, battery runtime and independently measured acoustic level near ear. Once-per-second serial telemetry supports threshold calibration, not sound exposure measurement.
- Privacy/security: BLE discovery and notification behavior when unpaired; retention behavior; no cloud traffic.
- Robustness: speaker feedback, wind, panting, scratching, vehicles and multiple barking dogs.

No benchmark numbers are asserted until the measurements actually exist.
