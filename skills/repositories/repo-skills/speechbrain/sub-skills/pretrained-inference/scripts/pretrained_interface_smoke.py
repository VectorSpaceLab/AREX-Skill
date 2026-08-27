#!/usr/bin/env python3
"""Inspect SpeechBrain pretrained inference interfaces without downloads."""

from __future__ import annotations

import argparse
import inspect
import json


def collect() -> dict:
    from speechbrain.inference.ASR import (
        EncoderASR,
        EncoderDecoderASR,
        StreamingASR,
        WhisperASR,
    )
    from speechbrain.inference.classifiers import AudioClassifier, EncoderClassifier
    from speechbrain.inference.enhancement import (
        SpectralMaskEnhancement,
        WaveformEnhancement,
    )
    from speechbrain.inference.interfaces import Pretrained, foreign_class
    from speechbrain.inference.separation import SepformerSeparation
    from speechbrain.inference.speaker import SpeakerRecognition
    from speechbrain.inference.text import GraphemeToPhoneme
    from speechbrain.inference.VAD import VAD
    from speechbrain.utils.fetching import FetchConfig, LocalStrategy

    targets = {
        "Pretrained.from_hparams": Pretrained.from_hparams,
        "Pretrained.load_audio": Pretrained.load_audio,
        "foreign_class": foreign_class,
        "EncoderDecoderASR.transcribe_file": EncoderDecoderASR.transcribe_file,
        "EncoderDecoderASR.transcribe_batch": EncoderDecoderASR.transcribe_batch,
        "EncoderASR.transcribe_file": EncoderASR.transcribe_file,
        "WhisperASR.transcribe_file": WhisperASR.transcribe_file,
        "StreamingASR.transcribe_file": StreamingASR.transcribe_file,
        "EncoderClassifier.classify_file": EncoderClassifier.classify_file,
        "EncoderClassifier.encode_batch": EncoderClassifier.encode_batch,
        "AudioClassifier.classify_batch": AudioClassifier.classify_batch,
        "SpeakerRecognition.verify_files": SpeakerRecognition.verify_files,
        "SpeakerRecognition.verify_batch": SpeakerRecognition.verify_batch,
        "SpectralMaskEnhancement.enhance_file": SpectralMaskEnhancement.enhance_file,
        "WaveformEnhancement.enhance_file": WaveformEnhancement.enhance_file,
        "SepformerSeparation.separate_file": SepformerSeparation.separate_file,
        "VAD.get_speech_segments": VAD.get_speech_segments,
        "GraphemeToPhoneme.g2p": GraphemeToPhoneme.g2p,
    }
    return {
        "signatures": {name: str(inspect.signature(obj)) for name, obj in targets.items()},
        "local_strategies": [item.name for item in LocalStrategy],
        "fetch_config_signature": str(inspect.signature(FetchConfig)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()
    result = collect()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, sig in result["signatures"].items():
            print(f"{name}: {sig}")
        print("LocalStrategy:", ", ".join(result["local_strategies"]))
        print("FetchConfig:", result["fetch_config_signature"])


if __name__ == "__main__":
    main()
