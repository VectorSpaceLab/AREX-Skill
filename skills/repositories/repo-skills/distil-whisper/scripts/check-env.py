#!/usr/bin/env python3
"""Check that the Distil-Whisper inspection stack is importable.

Safe by default: this script only imports packages, prints versions, and
reports the active backend. It does not download models or touch Hub state.

Example:
    python scripts/check-env.py
    python scripts/check-env.py --json
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib.metadata import version


def _safe_version(name: str) -> str:
    try:
        return version(name)
    except Exception as exc:  # pragma: no cover - only used for diagnostics
        return f"ERR:{exc}"


def _collect_info() -> dict:
    import accelerate
    import datasets
    import distil_whisper
    import evaluate
    import flax
    import jax
    import jiwer
    import soundfile
    import torch
    import transformers

    from distil_whisper import FlaxWhisperForConditionalGeneration, FlaxWhisperPipeline, InferenceState, PjitPartitioner

    return {
        "packages": {
            "distil_whisper": _safe_version("distil_whisper"),
            "torch": torch.__version__,
            "jax": jax.__version__,
            "flax": flax.__version__,
            "transformers": transformers.__version__,
            "datasets": datasets.__version__,
            "accelerate": accelerate.__version__,
            "evaluate": evaluate.__version__,
            "jiwer": _safe_version("jiwer"),
            "soundfile": soundfile.__version__,
        },
        "backend": {
            "torch_cuda_available": torch.cuda.is_available(),
            "jax_devices": [str(device) for device in jax.devices()],
        },
        "distil_whisper_exports": [
            name for name in dir(distil_whisper) if not name.startswith("_")
        ],
        "signatures": {
            "FlaxWhisperPipeline.__init__": str(inspect.signature(FlaxWhisperPipeline.__init__)),
            "FlaxWhisperPipeline.generate": str(inspect.signature(FlaxWhisperPipeline.generate)),
            "PjitPartitioner.__init__": str(inspect.signature(PjitPartitioner.__init__)),
            "InferenceState": str(inspect.signature(InferenceState)),
            "FlaxWhisperForConditionalGeneration": [
                name
                for name in ["from_pretrained", "pipeline_generate", "generate"]
                if hasattr(FlaxWhisperForConditionalGeneration, name)
            ],
        },
        "file": distil_whisper.__file__,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Distil-Whisper inspection environment.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    try:
        info = _collect_info()
    except Exception as exc:  # pragma: no cover - diagnostics only
        print(f"Environment check failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0

    print("Distil-Whisper inspection environment")
    for key, value in info["packages"].items():
        print(f"- {key}: {value}")
    print(f"- torch.cuda.is_available(): {info['backend']['torch_cuda_available']}")
    print(f"- jax.devices(): {', '.join(info['backend']['jax_devices'])}")
    print(f"- distil_whisper file: {info['file']}")
    print("- exported symbols:", ", ".join(info["distil_whisper_exports"]))
    print("- key signatures:")
    for key, value in info["signatures"].items():
        print(f"  * {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
