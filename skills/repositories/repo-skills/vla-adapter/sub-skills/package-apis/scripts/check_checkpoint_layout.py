#!/usr/bin/env python3
"""Check VLA-Adapter / Prismatic checkpoint layout without loading weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

HF_ASSET_HINTS = (
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "processor_config.json",
    "preprocessor_config.json",
    "generation_config.json",
)
HF_REMOTE_CODE_HINTS = (
    "configuration_prismatic.py",
    "modeling_prismatic.py",
    "processing_prismatic.py",
)
WEIGHT_PATTERNS = ("*.pt", "*.bin", "*.safetensors")


def report(level: str, msg: str) -> None:
    print(f"{level}: {msg}")


def check_exists(path: Path, label: str, required: bool = True) -> bool:
    if path.exists():
        report("PASS", f"{label}: {path.name}")
        return True
    report("FAIL" if required else "WARN", f"missing {label}: {path.name}")
    return not required


def load_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        report("FAIL", f"cannot parse {path.name}: {type(exc).__name__}: {exc}")
        return None

    if not isinstance(data, dict):
        report("FAIL", f"{path.name} is not a JSON object")
        return None

    report("PASS", f"{path.name} JSON keys: {sorted(data.keys())[:12]}")
    return data


def iter_weight_files(root: Path) -> Iterable[Path]:
    for pattern in WEIGHT_PATTERNS:
        yield from root.glob(pattern)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate checkpoint files for VLA-Adapter package workflows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--checkpoint", type=Path, required=True, help="Checkpoint or export directory to inspect")
    parser.add_argument("--expect-dataset-statistics", action="store_true", help="Require dataset_statistics.json")
    parser.add_argument("--expect-lora-adapter", action="store_true", help="Require lora_adapter/ layout")
    parser.add_argument("--expect-hf-config", action="store_true", help="Require HF-style config assets")
    args = parser.parse_args()

    ckpt = args.checkpoint
    ok = True

    ok &= check_exists(ckpt, "checkpoint directory") and ckpt.is_dir()
    if not ok:
        return 1

    config = ckpt / "config.json"
    ok &= check_exists(config, "config.json")
    config_data = load_json(config) if config.exists() else None
    if config_data is None:
        return 1

    if args.expect_hf_config:
        auto_map = config_data.get("auto_map")
        if isinstance(auto_map, dict):
            required_auto_map = {"AutoConfig", "AutoModelForVision2Seq"}
            missing_auto_map = sorted(required_auto_map - set(auto_map))
            if missing_auto_map:
                report("FAIL", "config.json is missing HF auto_map entries: " + ", ".join(missing_auto_map))
                ok = False
            else:
                report("PASS", f"auto_map entries: {sorted(auto_map.keys())}")
        else:
            report("FAIL", "config.json is missing HF auto_map metadata")
            ok = False

        if "model_type" in config_data:
            report("PASS", f"model_type: {config_data['model_type']}")
        else:
            report("WARN", "model_type is absent from config.json")

        hf_assets = [name for name in HF_ASSET_HINTS if (ckpt / name).exists()]
        remote_code = [name for name in HF_REMOTE_CODE_HINTS if (ckpt / name).exists()]
        if hf_assets:
            report("PASS", "HF asset hints: " + ", ".join(hf_assets))
        else:
            report("WARN", "no tokenizer / processor asset hints found at top level")
        if remote_code:
            report("PASS", "remote-code hints: " + ", ".join(remote_code))
        else:
            report("WARN", "no local remote-code files found at top level")
        if not (hf_assets or remote_code):
            report("FAIL", "HF config assets are missing from the export layout")
            ok = False

    stats = ckpt / "dataset_statistics.json"
    if args.expect_dataset_statistics:
        ok &= check_exists(stats, "dataset_statistics.json")
    if stats.exists():
        stats_data = load_json(stats)
        if stats_data is None:
            return 1
        if isinstance(stats_data, dict) and stats_data:
            report("PASS", f"dataset statistics entries: {len(stats_data)}")
        else:
            report("WARN", "dataset statistics is empty or not a dict")

    if args.expect_lora_adapter:
        lora_dir = ckpt / "lora_adapter"
        ok &= check_exists(lora_dir, "lora_adapter directory") and lora_dir.is_dir()
        if lora_dir.is_dir():
            adapter_config = lora_dir / "adapter_config.json"
            adapter_weights = [p for p in iter_weight_files(lora_dir) if p.name != "adapter_config.json"]
            ok &= check_exists(adapter_config, "adapter_config.json")
            if adapter_weights:
                report("PASS", f"adapter weight files: {len(adapter_weights)}")
            else:
                report("FAIL", "no adapter weight files found inside lora_adapter/")
                ok = False

    checkpoints_dir = ckpt / "checkpoints"
    if checkpoints_dir.exists():
        report("PASS", "checkpoints/ directory found")
        weight_files = list(iter_weight_files(checkpoints_dir))
        if weight_files:
            report("PASS", f"checkpoint weight candidates: {len(weight_files)}")
        else:
            report("WARN", "checkpoints/ exists but no .pt / .bin / .safetensors files were found")

    top_level_weights = list(iter_weight_files(ckpt))
    if top_level_weights:
        report("PASS", f"top-level weight candidates: {len(top_level_weights)}")
    elif not checkpoints_dir.exists():
        report("WARN", "no top-level weights or checkpoints/ directory found")

    report("Result", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
