#!/usr/bin/env python3
"""Create a tiny no-network LJ Speech fixture for metadata checks.

The fixture includes one valid PCM WAV, but it does not run the repository's
preprocessor or prove that the legacy audio/TensorFlow stack can process it.
"""
import argparse
import os
import sys
import wave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", help="Fixture directory to create")
    args = parser.parse_args()
    try:
        import numpy as np
    except ImportError:
        print("numpy is required", file=sys.stderr)
        return 2
    root = os.path.abspath(args.output_dir)
    data = os.path.join(root, "training")
    os.makedirs(data, exist_ok=True)
    linear = np.zeros((4, 1025), dtype=np.float32)
    mel = np.zeros((4, 80), dtype=np.float32)
    np.save(os.path.join(data, "linear-00001.npy"), linear, allow_pickle=False)
    np.save(os.path.join(data, "mel-00001.npy"), mel, allow_pickle=False)
    raw_root = os.path.join(root, "LJSpeech-1.1")
    raw = os.path.join(raw_root, "wavs")
    os.makedirs(raw, exist_ok=True)
    wav_path = os.path.join(raw, "LJ001-0001.wav")
    with wave.open(wav_path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(20000)
        handle.writeframes(b"\x00\x00" * 2000)
    with open(os.path.join(raw_root, "metadata.csv"), "w", encoding="utf-8") as handle:
        handle.write("LJ001-0001|unused|A tiny test sentence.\n")
    print("created fixture:", root)
    print("validate:", os.path.join(data, "train.txt"))
    print("audio fixture:", wav_path)
    print("scope: layout/metadata only; preprocessing and training not run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
