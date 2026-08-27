#!/usr/bin/env python3
"""Inspect ESPnet3 stage selection and required config flags without running stages."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT = ["create_dataset", "train_tokenizer", "collect_stats", "train", "infer", "measure", "pack_model", "upload_model", "pack_demo", "upload_demo"]
REQ = {
    "create_dataset": ["training_config"],
    "train_tokenizer": ["training_config"],
    "collect_stats": ["training_config"],
    "train": ["training_config"],
    "infer": ["inference_config"],
    "measure": ["metrics_config"],
    "pack_model": ["training_config", "publication_config"],
    "upload_model": ["publication_config"],
    "pack_demo": ["demo_config"],
    "upload_demo": ["demo_config"],
}


def resolve(requested: list[str]) -> list[str]:
    if "all" in requested:
        return DEFAULT[:]
    bad = [stage for stage in requested if stage not in DEFAULT]
    if bad:
        raise ValueError(f"unknown stages: {bad}")
    return requested


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve ESPnet3 stages and config requirements.")
    parser.add_argument("--stages", nargs="+", default=["all"])
    for name in ["training_config", "inference_config", "metrics_config", "publication_config", "demo_config"]:
        parser.add_argument("--" + name.replace("_", "-"), dest=name)
    parser.add_argument("--strict-files", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        stages = resolve(args.stages)
        missing = sorted({required for stage in stages for required in REQ[stage] if getattr(args, required) is None})
        missing_files = [required for required in ["training_config", "inference_config", "metrics_config", "publication_config", "demo_config"] if getattr(args, required) and not Path(getattr(args, required)).exists()]
        ok = not missing and (not args.strict_files or not missing_files)
        payload = {"ok": ok, "stages": stages, "missing_config_flags": missing, "missing_files": missing_files}
    except Exception as exc:  # noqa: BLE001 - report stage/config validation error.
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PASS" if payload["ok"] else "FAIL")
        for key, value in payload.items():
            if key != "ok":
                print(f"{key}: {value}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
