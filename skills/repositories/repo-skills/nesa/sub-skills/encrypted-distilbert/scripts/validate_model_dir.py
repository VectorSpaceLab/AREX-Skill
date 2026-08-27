#!/usr/bin/env python3
"""Validate a local encrypted DistilBERT-style model directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TOKENIZER_CANDIDATES = ["tokenizer.json", "vocab.txt", "tokenizer.model", "spiece.model"]
WEIGHT_CANDIDATES = ["model.safetensors", "pytorch_model.bin", "tf_model.h5", "flax_model.msgpack"]
REQUIRED_SMALL = ["config.json", "tokenizer_config.json", "special_tokens_map.json"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local model files before running the Nesa encrypted DistilBERT demo.")
    parser.add_argument("model_dir", type=Path, help="Directory containing config, tokenizer files, and model weights.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    model_dir = args.model_dir.expanduser().resolve()
    report = {"model_dir": str(model_dir), "exists": model_dir.is_dir(), "checks": {}, "id2label": None}

    if not model_dir.is_dir():
        report["error"] = "model_dir is not a directory"
    else:
        for name in REQUIRED_SMALL:
            report["checks"][name] = (model_dir / name).is_file()
        report["checks"]["tokenizer_artifact"] = [name for name in TOKENIZER_CANDIDATES if (model_dir / name).is_file()]
        report["checks"]["weight_artifact"] = [name for name in WEIGHT_CANDIDATES if (model_dir / name).is_file()]
        try:
            config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
            report["id2label"] = config.get("id2label")
            report["model_type"] = config.get("model_type")
            report["num_labels"] = config.get("num_labels")
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            report["config_error"] = f"{type(exc).__name__}: {exc}"

    ok = bool(
        report.get("exists")
        and all(report["checks"].get(name) for name in REQUIRED_SMALL)
        and report["checks"].get("tokenizer_artifact")
        and report["checks"].get("weight_artifact")
    )
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Model directory: {model_dir}")
        print(f"Exists: {report['exists']}")
        for key, value in report.get("checks", {}).items():
            print(f"{key}: {value}")
        if report.get("id2label") is not None:
            print(f"id2label: {report['id2label']}")
        if report.get("config_error"):
            print(f"config_error: {report['config_error']}")
        print(f"OK: {ok}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
