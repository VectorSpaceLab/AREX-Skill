#!/usr/bin/env python3
"""Tiny pretrained-inference smoke check for Asteroid.

This script creates a tiny ConvTasNet, round-trips it through serialize /
from_pretrained, runs tensor separation, and exercises the file-based path on a
synthetic WAV file.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from asteroid.models import ConvTasNet


def build_model() -> ConvTasNet:
    return ConvTasNet(
        n_src=2,
        n_repeats=1,
        n_blocks=1,
        bn_chan=8,
        hid_chan=4,
        skip_chan=4,
        n_filters=16,
        sample_rate=8000,
    ).eval()


def main() -> None:
    model = build_model()
    model_conf = model.serialize()
    reloaded = ConvTasNet.from_pretrained(model_conf).eval()

    wav = torch.randn(1, 400)
    out = reloaded.separate(wav)
    print(f"tensor-separate: {tuple(out.shape)} on {out.device}")

    if torch.cuda.is_available():
        cuda_model = build_model().cuda().eval()
        cuda_out = cuda_model.separate(wav.to("cuda"))
        print(f"cuda-separate: {tuple(cuda_out.shape)} on {cuda_out.device}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        wav_path = tmpdir / "tiny.wav"
        sf.write(wav_path.as_posix(), np.random.randn(8000).astype("float32"), 8000)
        reloaded.separate(wav_path.as_posix(), force_overwrite=True)
        written = sorted(tmpdir.glob("tiny_est*.wav"))
        print(f"file-separate: {len(written)} files written")


if __name__ == "__main__":
    main()
