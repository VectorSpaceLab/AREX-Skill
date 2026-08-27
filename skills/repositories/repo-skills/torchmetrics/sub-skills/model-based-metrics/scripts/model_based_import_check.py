#!/usr/bin/env python3
"""Check model-based TorchMetrics imports and signatures without downloads."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<signature unavailable: {exc.__class__.__name__}: {exc}>"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Return a nonzero exit code if any model-based class cannot be imported.",
    )
    args = parser.parse_args(argv)

    try:
        import torchmetrics
        from torchmetrics.audio import DeepNoiseSuppressionMeanOpinionScore, NonIntrusiveSpeechQualityAssessment
        from torchmetrics.image import (
            DeepImageStructureAndTextureSimilarity,
            FrechetInceptionDistance,
            InceptionScore,
            KernelInceptionDistance,
            LearnedPerceptualImagePatchSimilarity,
            MemorizationInformedFrechetInceptionDistance,
            PerceptualPathLength,
        )
        from torchmetrics.multimodal import CLIPImageQualityAssessment, CLIPScore, LipVertexError
        from torchmetrics.text import BERTScore, InfoLM
        from torchmetrics.video import VideoMultiMethodAssessmentFusion
        from torchmetrics.utilities import imports as tm_imports
    except Exception as exc:  # pragma: no cover - user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    classes = {
        "BERTScore": BERTScore,
        "InfoLM": InfoLM,
        "CLIPScore": CLIPScore,
        "CLIPImageQualityAssessment": CLIPImageQualityAssessment,
        "LipVertexError": LipVertexError,
        "FrechetInceptionDistance": FrechetInceptionDistance,
        "KernelInceptionDistance": KernelInceptionDistance,
        "InceptionScore": InceptionScore,
        "MemorizationInformedFrechetInceptionDistance": MemorizationInformedFrechetInceptionDistance,
        "LearnedPerceptualImagePatchSimilarity": LearnedPerceptualImagePatchSimilarity,
        "DeepImageStructureAndTextureSimilarity": DeepImageStructureAndTextureSimilarity,
        "PerceptualPathLength": PerceptualPathLength,
        "DeepNoiseSuppressionMeanOpinionScore": DeepNoiseSuppressionMeanOpinionScore,
        "NonIntrusiveSpeechQualityAssessment": NonIntrusiveSpeechQualityAssessment,
        "VideoMultiMethodAssessmentFusion": VideoMultiMethodAssessmentFusion,
    }

    optional_flags = {
        "transformers": bool(tm_imports._TRANSFORMERS_AVAILABLE),
        "bert_score": bool(tm_imports._BERTSCORE_AVAILABLE),
        "piq>=0.8": bool(tm_imports._PIQ_GREATER_EQUAL_0_8),
        "torchvision": bool(tm_imports._TORCHVISION_AVAILABLE),
        "torch_fidelity": bool(tm_imports._TORCH_FIDELITY_AVAILABLE),
        "librosa": bool(tm_imports._LIBROSA_AVAILABLE),
        "onnxruntime": bool(tm_imports._ONNXRUNTIME_AVAILABLE),
        "requests": bool(tm_imports._REQUESTS_AVAILABLE),
        "vmaf_torch": bool(tm_imports._TORCH_VMAF_AVAILABLE),
    }

    missing: list[str] = []
    signatures = {name: safe_signature(cls.__init__) for name, cls in classes.items()}

    payload = {
        "status": "ok",
        "torchmetrics_version": getattr(torchmetrics, "__version__", "unknown"),
        "optional_dependencies": optional_flags,
        "signatures": signatures,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.fail_on_missing and missing:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
