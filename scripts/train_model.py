#!/usr/bin/env python3
"""Train an owner-labeled bark-event classifier; export C++ inference.

Requires numpy and scikit-learn. The source is one 16kHz mono 16-bit WAV
per observationally labeled recording (CSV path,label,motion_g). Entire
recordings, not frames, are split between training and held-out validation.
"""
from pathlib import Path
import argparse
import csv
import math
import wave
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

LABELS = ("alert", "attention", "play", "uncertain")
WINDOW = 512

def features(audio: np.ndarray, motion: float) -> np.ndarray:
    s = audio.astype(np.float64)
    rms = float(np.sqrt(np.mean(s * s)))
    zcr = float(np.mean((audio[:-1] >= 0) != (audio[1:] >= 0)))
    crest = float(np.max(np.abs(s)) / max(rms, 1.0))
    return np.asarray([rms, zcr, crest, motion], dtype=np.float32)

def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        properties = (w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getcomptype())
        if properties != (16000, 1, 2, "NONE"):
            raise ValueError(f"{path}: WAV must be 16kHz mono PCM16; got {properties}")
        n = w.getnframes()
        if not WINDOW <= n <= 16000 * 120:
            raise ValueError(f"{path}: file must be 32 ms to 120 s")
        return np.frombuffer(w.readframes(n), dtype="<i2").copy()

def load_dataset(index: Path):
    xs, ys, groups, file_labels = [], [], [], []
    with index.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"path", "label", "motion_g"}.issubset(reader.fieldnames):
            raise ValueError("CSV requires path,label,motion_g columns")
        rows = list(reader)
    if len(rows) < 10:
        raise ValueError("Collect >=10 distinct owner-labeled recordings first")
    totals = {label: 0 for label in LABELS}
    for i, row in enumerate(rows):
        label = row["label"].strip().lower()
        if label not in LABELS:
            raise ValueError(f"Line {i+2}: invalid label {label}")
        totals[label] += 1
        file_labels.append(LABELS.index(label))
        motion = float(row["motion_g"])
        if not math.isfinite(motion) or not 0 <= motion <= 10:
            raise ValueError(f"Line {i+2}: motion_g must be finite, 0..10")
        path = (index.parent / row["path"]).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        samples = read_wav(path)
        windows = min(len(samples) // WINDOW, 100)
        for j in range(windows):
            segment = samples[j*WINDOW:(j+1)*WINDOW]
            xs.append(features(segment, motion))
            ys.append(LABELS.index(label))
            groups.append(i)
    if min(totals.values()) < 2:
        raise ValueError("Each of the four labels needs at least two recordings")
    return np.stack(xs), np.asarray(ys), np.asarray(groups), np.asarray(file_labels), totals

def cpp_float(value: float) -> str:
    s = format(float(value), ".10g")
    if "e" not in s.lower() and "." not in s:
        s += ".0"
    return s + "f"

def export_header(model: DecisionTreeClassifier, output: Path) -> None:
    tree = model.tree_
    children_left = tree.children_left.tolist()
    children_right = tree.children_right.tolist()
    feature = tree.feature.tolist()
    threshold = tree.threshold.tolist()
    classes = model.classes_.tolist()
    choices, probabilities = [], []
    for i in range(tree.node_count):
        distribution = tree.value[i][0].astype(float)
        total = distribution.sum()
        idx = int(np.argmax(distribution))
        choices.append(int(classes[idx]))
        probabilities.append(float(distribution[idx]/total) if total else 0.0)
    def ints(v): return ", ".join(str(int(x)) for x in v)
    def floats(v): return ", ".join(cpp_float(x) for x in v)
    payload = (
        "// Generated from private training data; no recordings stored here.\n"
        "#pragma once\n"
        "namespace DogModel {\n"
        "static constexpr bool READY = true;\n"
        f"static constexpr int N = {tree.node_count};\n"
        f"static constexpr int L[N] = {{{ints(children_left)}}};\n"
        f"static constexpr int R[N] = {{{ints(children_right)}}};\n"
        f"static constexpr int F[N] = {{{ints(feature)}}};\n"
        f"static constexpr float T[N] = {{{floats(threshold)}}};\n"
        f"static constexpr int C[N] = {{{ints(choices)}}};\n"
        f"static constexpr float P[N] = {{{floats(probabilities)}}};\n"
        'static constexpr const char* LABELS[4] = {"alert","attention","play","uncertain"};\n'
        "inline const char* predict(const float x[4], float& confidence) {\n"
        "  int n = 0;\n"
        "  while (L[n] >= 0) n = x[F[n]] <= T[n] ? L[n] : R[n];\n"
        "  confidence = P[n];\n"
        "  return LABELS[C[n]];\n"
        "}\n"
        "}\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload, encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("include/model_enabled.h"))
    args = p.parse_args()
    X, y, groups, file_labels, totals = load_dataset(args.index)
    file_ids = np.arange(len(file_labels))
    held_file_count = max(len(LABELS), math.ceil(len(file_labels) * 0.25))
    train_ids, held_ids = train_test_split(
        file_ids, test_size=held_file_count, random_state=918,
        stratify=file_labels,
    )
    train = np.flatnonzero(np.isin(groups, train_ids))
    held = np.flatnonzero(np.isin(groups, held_ids))
    if len(set(y[train])) != len(LABELS):
        raise ValueError("Train split dropped a class; collect more distinct recordings")
    model = DecisionTreeClassifier(max_depth=6, min_samples_leaf=4, random_state=918)
    model.fit(X[train], y[train])
    predictions = model.predict(X[held])
    accuracy = float(np.mean(predictions == y[held]))
    print("Recordings per class:", totals)
    print("Train recordings:", len(np.unique(groups[train])))
    print("Held-out recordings:", len(np.unique(groups[held])))
    print("Held-out window accuracy:", round(accuracy, 4))
    print("Note: this is NOT dog-intent validation; test on new sessions and dogs.")
    export_header(model, args.out)
    print("Generated:", args.out)

if __name__ == "__main__":
    main()
