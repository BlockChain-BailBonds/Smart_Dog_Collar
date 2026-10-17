"""Synthetic-only tests: no pet recordings, hardware or external network."""
import csv
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / 'scripts' / 'train_model.py'


class ReferenceManifestTest(unittest.TestCase):
    def test_manifest_gpio_matches_firmware(self):
        cfg = json.loads((ROOT / 'config' / 'hardware_reference.json').read_text())
        pins = cfg['interfaces']
        expected = {'MIC_BCLK': pins['microphone']['gpio']['bclk'],
                    'MIC_WS': pins['microphone']['gpio']['ws'],
                    'MIC_DIN': pins['microphone']['gpio']['din'],
                    'AMP_BCLK': pins['amplifier']['gpio']['bclk'],
                    'AMP_WS': pins['amplifier']['gpio']['ws'],
                    'AMP_DOUT': pins['amplifier']['gpio']['dout'],
                    'I2C_SDA': pins['motion']['gpio']['sda'],
                    'I2C_SCL': pins['motion']['gpio']['scl']}
        cpp = (ROOT / 'src' / 'main.cpp').read_text()
        for name, number in expected.items():
            self.assertIn(f'constexpr int {name} = {number};', cpp)
        self.assertEqual(len(set(expected.values())), len(expected))
        self.assertFalse(cfg['transport']['bluetooth']['default_enabled'])
        self.assertFalse(cfg['speech']['acoustic_output_measured'])
        self.assertEqual(cfg['detector']['frame_samples'], 512)


class SyntheticTrainingTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('collar_training', TRAIN)
        self.training = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.training)

    def test_float_literals_emit_valid_cpp(self):
        self.assertEqual(self.training.cpp_float(10), '10.0f')
        self.assertEqual(self.training.cpp_float(-2), '-2.0f')
        self.assertEqual(self.training.cpp_float(0.75), '0.75f')

    def test_dataset_and_export_with_independent_recording_split(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            index = directory / 'index.csv'
            with index.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['path', 'label', 'motion_g'])
                for label_index, label in enumerate(self.training.LABELS):
                    for recording in range(3):
                        path = directory / f'{label}_{recording}.wav'
                        samples = []
                        for i in range(1536):
                            amplitude = 800 + label_index * 1250 + recording * 75
                            sample = int(amplitude * math.sin(i * (0.09 + label_index * 0.025)))
                            samples.append(sample)
                        with wave.open(str(path), 'wb') as wav:
                            wav.setnchannels(1)
                            wav.setsampwidth(2)
                            wav.setframerate(16000)
                            wav.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
                        writer.writerow([path.name, label, f'{label_index * 0.07:.2f}'])
            X, y, group, file_labels, totals = self.training.load_dataset(index)
            self.assertEqual(len(file_labels), 12)
            self.assertEqual(len(X), 36)
            self.assertEqual(len(set(group)), 12)
            self.assertEqual(sum(totals.values()), 12)
            destination = directory / 'trained.h'
            complete = subprocess.run([sys.executable, str(TRAIN), '--index', str(index),
                                       '--out', str(destination)], capture_output=True,
                                      text=True, check=True)
            self.assertIn('Held-out window accuracy:', complete.stdout)
            header = destination.read_text()
            self.assertIn('static constexpr bool READY = true;', header)
            self.assertIn('inline const char* predict(', header)
            if shutil.which('g++'):
                test_source = directory / 'verify.cpp'
                test_source.write_text('#include "trained.h"\n'
                                       'int main() { float c=0; float f[4]={0,0,0,0};'
                                       ' return DogModel::predict(f,c)==nullptr; }\n')
                subprocess.run(['g++', '-std=c++11', '-Wall', '-Werror', '-fsyntax-only',
                                str(test_source)], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
