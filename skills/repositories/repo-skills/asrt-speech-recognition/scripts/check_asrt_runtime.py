#!/usr/bin/env python3
"""Check an ASRT Python runtime without mutating it.

This helper is safe to run from a user's ASRT source tree or with --asrt-root.
It imports selected modules, reports dependency versions, and optionally runs
small checks that do not require speech corpora, trained weights, or servers.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, List


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def import_status(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import failures clearly
        return {"module": module_name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module_name, "ok": True, "file": getattr(module, "__file__", None)}


def run_smokes() -> Dict[str, Any]:
    smokes: Dict[str, Any] = {}
    try:
        import numpy as np
        from language_model3 import ModelLanguage
        from speech_features import Spectrogram
        from model_zoo.speech_model.keras_backend import SpeechModel251BN
        from utils.config import load_pinyin_dict

        dict_path = Path("dict.txt")
        if dict_path.is_file():
            pinyin_list, pinyin_dict = load_pinyin_dict(str(dict_path))
            smokes["pinyin_count"] = len(pinyin_list)
            smokes["has_ni3"] = "ni3" in pinyin_dict
        else:
            smokes["pinyin_count"] = "skipped: dict.txt not found"

        if Path("model_language/language_model1.txt").is_file() and Path("model_language/language_model2.txt").is_file():
            ml = ModelLanguage("model_language")
            ml.load_model()
            smokes["language_sample"] = ml.pinyin_to_text(["ni3", "hao3", "ya5"])
        else:
            smokes["language_sample"] = "skipped: model_language files not found"

        wave = np.zeros((1, 16000), dtype=np.int16)
        smokes["spectrogram_shape_1s_16k_zero"] = list(Spectrogram().run(wave, 16000).shape)
        try:
            Spectrogram().run(wave, 8000)
        except Exception as exc:  # noqa: BLE001
            smokes["spectrogram_8k_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"

        model = SpeechModel251BN()
        smokes["speech_model_251bn"] = {
            "model_name": model.get_model_name(),
            "input_shape": list(model.input_shape),
            "output_shape": list(model.output_shape),
        }
    except Exception as exc:  # noqa: BLE001
        smokes["error"] = f"{type(exc).__name__}: {exc}"
    return smokes


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect ASRT dependency/module import status and optional tiny CPU-safe smokes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--asrt-root", help="ASRT source/module root to prepend to PYTHONPATH and use as working directory.")
    parser.add_argument("--skip-smokes", action="store_true", help="Only report versions/imports; do not instantiate models or run tiny checks.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.asrt_root:
        root = Path(args.asrt_root).expanduser().resolve()
        sys.path.insert(0, str(root))
        os.chdir(root)

    report: Dict[str, Any] = {
        "python": sys.version,
        "cwd": os.getcwd(),
        "distributions": {name: dist_version(name) for name in [
            "tensorflow", "tensorflow-cpu", "tensorflow-gpu", "numpy", "scipy", "matplotlib", "Flask", "waitress", "requests", "grpcio", "protobuf", "h5py"
        ]},
        "imports": [import_status(name) for name in [
            "utils.ops", "utils.config", "speech_features", "language_model3", "model_zoo.speech_model.keras_backend", "speech_model"
        ]],
    }
    if not args.skip_smokes:
        report["smokes"] = run_smokes()

    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    failed_imports = [item for item in report["imports"] if not item["ok"]]
    if failed_imports:
        return 1
    if isinstance(report.get("smokes"), dict) and "error" in report["smokes"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
