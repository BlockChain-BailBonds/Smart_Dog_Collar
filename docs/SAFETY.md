# Safety, animal welfare, and responsible claims

**BENCH PROTOTYPE ONLY.** This project is not a finished consumer wearable, tracking device, medical instrument or certified dog translator.

- **Animal hearing:** 8 Ω 1 W is a component rating, not an approved output volume. Keep amplified sound away from ears, start at low gain, measure acoustic exposure and avoid repeated startling utterances.
- **Electrical:** Li-ion cells can burn. A TP4056 charging module alone is insufficient for an animal-worn system. Use rated protection, temperature sensing, overcurrent cutoff, correct charge regulation, safe power-source isolation, strain relief and appropriate enclosure sealing/venting. Charge off-animal.
- **Mechanical:** prevent choking, entanglement, chewing, battery access, sharp edges, skin rubbing and snagging. Use a suitable breakaway/release mechanism. Do not obstruct breathing or normal movement.
- **Thermal/wet:** verify charging and RF/audio load heating; guard against drool/rain ingress. Electronic housings cannot be assumed waterproof based on a 3D model.
- **Biometrics:** MAX86150/PPG/ECG requires reliable optical/electrical contact, which canine fur often prevents. No vital-sign or emergency alerts are implemented or validated. Consult veterinarians for distress/health concerns.
- **Privacy:** recordings can include voices, places and identifiers. Keep local, redact, and obtain consent where required. BLE broadcasts may be observable; no BLE security/pairing exists in this reference, so BLE is off by default.
- **Training labels:** language-like speech is a convenience for owners, not evidence of a dog's meaning. Never substitute model outputs for direct observation or veterinary care.

Before any supervised animal fitting, obtain independent review of electrical, acoustic and mechanical risks. There is no automatically safe deployment merely because firmware compiles.
