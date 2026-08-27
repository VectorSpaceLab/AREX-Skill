#!/usr/bin/env python3
"""Smoke-check an installed SpeechBrain environment without downloads.

This script intentionally uses synthetic data and local imports only. It is safe
for CPU-only environments and reports CUDA availability without requiring it.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import tempfile
from pathlib import Path


def check() -> dict:
    import torch
    import speechbrain as sb
    from speechbrain.dataio import audio_io
    from speechbrain.inference.ASR import EncoderASR, EncoderDecoderASR
    from speechbrain.inference.classifiers import EncoderClassifier
    from speechbrain.inference.enhancement import (
        SpectralMaskEnhancement,
        WaveformEnhancement,
    )
    from speechbrain.inference.separation import SepformerSeparation
    from speechbrain.inference.speaker import SpeakerRecognition
    from speechbrain.inference.text import GraphemeToPhoneme
    from speechbrain.inference.VAD import VAD
    from speechbrain.utils.run_opts import RunOptions

    modules = [
        "speechbrain.core",
        "speechbrain.dataio.dataset",
        "speechbrain.dataio.audio_io",
        "speechbrain.inference",
        "speechbrain.augment.time_domain",
        "speechbrain.processing.features",
        "speechbrain.lobes.features",
        "speechbrain.decoders.ctc",
        "speechbrain.nnet.losses",
        "speechbrain.utils.metric_stats",
    ]
    imported = []
    for name in modules:
        importlib.import_module(name)
        imported.append(name)

    filename, run_opts, overrides = RunOptions.from_command_line_args(
        ["params.yaml", "--device=cpu", "--seed=3"]
    )

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        wave = torch.zeros(1, 1600)
        audio_io.save(path, wave, 16000)
        loaded, sr = audio_io.load(path)
        info = audio_io.info(path)
        audio = {
            "sample_rate": sr,
            "shape": list(loaded.shape),
            "duration": info.duration,
            "format": info.format,
        }
    finally:
        Path(path).unlink(missing_ok=True)

    pretrained_classes = [
        EncoderASR,
        EncoderDecoderASR,
        EncoderClassifier,
        SpeakerRecognition,
        SepformerSeparation,
        SpectralMaskEnhancement,
        WaveformEnhancement,
        VAD,
        GraphemeToPhoneme,
    ]

    return {
        "speechbrain_version": sb.__version__,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "imported_modules": imported,
        "run_options_probe": {
            "filename": filename,
            "device": run_opts["device"],
            "overrides": overrides,
        },
        "audio_io_roundtrip": audio,
        "pretrained_classes": [cls.__name__ for cls in pretrained_classes],
        "from_hparams_signature": str(
            inspect.signature(EncoderDecoderASR.from_hparams)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a short text summary.",
    )
    args = parser.parse_args()
    result = check()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"SpeechBrain {result['speechbrain_version']} imported")
        print(f"Torch {result['torch_version']} CUDA={result['cuda_available']}")
        print(
            "Audio roundtrip:",
            result["audio_io_roundtrip"]["sample_rate"],
            result["audio_io_roundtrip"]["shape"],
        )
        print("Pretrained classes:", ", ".join(result["pretrained_classes"]))


if __name__ == "__main__":
    main()
