#!/usr/bin/env python3
"""Generate 22050 Hz, mono, signed 16-bit raw PCM from local eSpeak.

No external synthesis API, account, or speech data upload is required.
Use short, owner-approved phrases; no dog emotion is asserted as fact.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import wave
from io import BytesIO

DEFAULT_PHRASES = {
    "bark": "I am barking.",
    "alert": "I might be alerting you.",
    "attention": "I might want attention.",
    "play": "I might want to play.",
}

def synthesize(phrase: str, speed: int) -> bytes:
    if not shutil.which("espeak"):
        raise RuntimeError("eSpeak executable missing. Install espeak first.")
    completed = subprocess.run(
        ["espeak", "--stdout", "-s", str(speed), phrase],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    with wave.open(BytesIO(completed.stdout), "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        if (rate, channels, width) != (22050, 1, 2):
            raise ValueError(f"Expected 22050 Hz mono 16-bit WAV, got {rate}/{channels}/{width}")
        pcm = w.readframes(w.getnframes())
    return pcm

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data"))
    parser.add_argument("--speed", type=int, default=175)
    args = parser.parse_args()
    if not 110 <= args.speed <= 260:
        parser.error("--speed must be between 110 and 260")
    args.out.mkdir(parents=True, exist_ok=True)
    for name, phrase in DEFAULT_PHRASES.items():
        data = synthesize(phrase, args.speed)
        if len(data) > 300_000:
            raise RuntimeError(f"Phrase {name} is too large")
        target = args.out / (name + ".pcm")
        target.write_bytes(data)
        print(f"{target}: {len(data)} bytes")
    print("Upload these assets with: pio run -t uploadfs")

if __name__ == "__main__":
    main()
