#!/usr/bin/env python3
"""Summarize expected Ludwig model artifact files without loading large weights."""
import argparse
import json
from pathlib import Path

EXPECTED = ["model_hyperparameters.json", "training_set_metadata.json", "model_weights.safetensors", "model_weights"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a directory looks like a Ludwig model artifact.")
    parser.add_argument("--model-dir", required=True)
    args = parser.parse_args()
    model_dir = Path(args.model_dir)
    result = {"model_dir": str(model_dir), "exists": model_dir.exists(), "files": {}}
    for name in EXPECTED:
        result["files"][name] = (model_dir / name).exists()
    result["has_weights"] = result["files"].get("model_weights.safetensors") or result["files"].get("model_weights")
    result["looks_like_ludwig_model"] = result["exists"] and result["files"].get("model_hyperparameters.json") and result["files"].get("training_set_metadata.json") and result["has_weights"]
    print(json.dumps(result, indent=2))
    return 0 if result["looks_like_ludwig_model"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
