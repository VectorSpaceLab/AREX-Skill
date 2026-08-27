#!/usr/bin/env python3
"""Run deterministic TorchMetrics audio and text smoke checks without downloads."""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


def as_python(value: Any) -> Any:
    import torch

    if isinstance(value, torch.Tensor):
        value = value.detach().cpu()
        if value.numel() == 1:
            return value.item()
        return value.tolist()
    if isinstance(value, dict):
        return {key: as_python(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_python(val) for val in value]
    return value


def run_audio() -> dict[str, Any]:
    import torch
    from torchmetrics.audio import PerceptualEvaluationSpeechQuality, SignalNoiseRatio

    torch.manual_seed(1234)
    fs = 16000
    target = torch.sin(torch.linspace(0, 2 * math.pi, fs))
    preds = target + 0.01 * torch.randn_like(target)

    snr = SignalNoiseRatio()
    pesq = PerceptualEvaluationSpeechQuality(fs=fs, mode="wb")

    snr_value = snr(preds, target)
    pesq_value = pesq(target, preds)
    if not torch.isfinite(snr_value):
        raise RuntimeError(f"SNR smoke returned {snr_value}")
    if not torch.isfinite(pesq_value):
        raise RuntimeError(f"PESQ smoke returned {pesq_value}")

    return {
        "snr": snr_value,
        "pesq": pesq_value,
    }


def run_text() -> dict[str, Any]:
    import torch
    from torchmetrics.text import BLEUScore, CharErrorRate, Perplexity, ROUGEScore, SacreBLEUScore, WordErrorRate

    bleu = BLEUScore()
    rouge = ROUGEScore(use_stemmer=False)
    sacre = SacreBLEUScore()
    wer = WordErrorRate()
    cer = CharErrorRate()
    perp = Perplexity(ignore_index=-100)

    preds = ["the cat sat on the mat"]
    target_refs = [["the cat is on the mat", "a cat is on the mat"]]
    reference = ["the cat is on the mat"]

    logits = torch.tensor(
        [
            [[4.0, 1.0, 0.1], [0.2, 3.0, 0.1], [0.1, 0.2, 4.0]],
            [[0.1, 2.5, 0.2], [2.5, 0.1, 0.1], [0.2, 0.2, 3.5]],
        ]
    )
    target = torch.tensor([[0, 1, 2], [1, 0, 2]])

    outputs = {
        "bleu": bleu(preds, target_refs),
        "rouge": rouge(preds=preds, target=reference),
        "sacrebleu": sacre(preds, target_refs),
        "wer": wer(["this is the prediction"], ["this is the reference"]),
        "cer": cer(["kitten"], ["sitting"]),
        "perplexity": perp(logits, target),
    }

    for name, value in outputs.items():
        if not torch.isfinite(value if isinstance(value, torch.Tensor) else value["rouge1_fmeasure"]):
            raise RuntimeError(f"{name} smoke returned a non-finite value")

    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", action="store_true", help="Run audio checks.")
    parser.add_argument("--text", action="store_true", help="Run text checks.")
    parser.add_argument("--all", action="store_true", help="Run both audio and text checks.")
    args = parser.parse_args(argv)

    try:
        import torchmetrics
    except Exception as exc:  # pragma: no cover - user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    run_audio_checks = args.all or args.audio or not args.text
    run_text_checks = args.all or args.text or not args.audio

    summary: dict[str, Any] = {
        "torchmetrics_version": getattr(torchmetrics, "__version__", "unknown"),
        "audio": None,
        "text": None,
    }

    try:
        if run_audio_checks:
            summary["audio"] = as_python(run_audio())
        if run_text_checks:
            summary["text"] = as_python(run_text())
    except Exception as exc:  # pragma: no cover - user-facing failure report
        print(f"SMOKE_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
