#!/usr/bin/env python3
"""Safely inspect a LitGPT or Hugging Face checkpoint directory layout.

This checker only reads directory entries and small JSON/YAML metadata. It never
loads model weights, downloads files, starts training, or writes outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    yaml = None


def parse_scalar_yaml_value(raw_value: str) -> Any:
    value = raw_value.strip()
    lower_value = value.lower()
    if lower_value in {"true", "false"}:
        return lower_value == "true"
    if lower_value in {"null", "none", "~"}:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml_mapping(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped or stripped.startswith("-"):
            raise ValueError("fallback YAML parser only supports simple key: value mappings")
        key, raw_value = stripped.split(":", 1)
        key = key.strip().strip("'\"")
        if not key:
            raise ValueError("fallback YAML parser found an empty key")
        result[key] = parse_scalar_yaml_value(raw_value)
    return result


TOKENIZER_FILE_NAMES = ("tokenizer.json", "tokenizer.model")
HF_INDEX_FILE_NAMES = ("pytorch_model.bin.index.json", "model.safetensors.index.json")


def file_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    if path.is_file():
        return {"exists": True, "kind": "file", "size_bytes": path.stat().st_size}
    if path.is_dir():
        return {"exists": True, "kind": "directory"}
    return {"exists": True, "kind": "other"}


def parse_metadata(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, None
    if path.stat().st_size > 2_000_000:
        return None, "metadata file is too large for this safe checker"
    try:
        if path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8")), None
        if path.suffix in {".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8")
            if yaml is None:
                return parse_simple_yaml_mapping(text), None
            data = yaml.safe_load(text)
            return data if isinstance(data, dict) else {}, None
    except Exception as exc:  # noqa: BLE001 - diagnostics should report parse errors
        return None, str(exc)
    return None, None


def collect_weight_files(checkpoint_dir: Path) -> dict[str, list[str]]:
    return {
        "litgpt": sorted(p.name for p in checkpoint_dir.glob("lit_model.pth")),
        "lora": sorted(p.name for p in checkpoint_dir.glob("lit_model.pth.lora")),
        "hf_bin": sorted(p.name for p in checkpoint_dir.glob("*.bin") if p.name != "training_args.bin"),
        "hf_safetensors": sorted(p.name for p in checkpoint_dir.glob("*.safetensors")),
        "hf_index": sorted(name for name in HF_INDEX_FILE_NAMES if (checkpoint_dir / name).is_file()),
    }


def classify(checkpoint_dir: Path, weights: dict[str, list[str]], has_config: bool, has_tokenizer: bool) -> str:
    if not checkpoint_dir.exists():
        return "missing-path"
    if not checkpoint_dir.is_dir():
        return "not-directory"
    has_litgpt = bool(weights["litgpt"])
    has_lora = bool(weights["lora"])
    has_hf = bool(weights["hf_bin"] or weights["hf_safetensors"] or weights["hf_index"])
    if has_litgpt and has_config:
        if has_lora:
            return "litgpt-merged-lora"
        return "litgpt-ready"
    if has_lora:
        return "litgpt-lora"
    if has_hf:
        return "huggingface-needs-conversion"
    if has_tokenizer and not has_litgpt:
        return "tokenizer-only"
    if has_config:
        return "config-only-or-incomplete"
    return "unknown-or-incomplete"


def build_report(checkpoint_dir: Path, mode: str, model_filename: str) -> dict[str, Any]:
    checkpoint_dir = checkpoint_dir.expanduser()
    exists = checkpoint_dir.exists()
    is_dir = checkpoint_dir.is_dir()

    files: dict[str, Any] = {
        "checkpoint_dir": file_info(checkpoint_dir),
        "model_config.yaml": file_info(checkpoint_dir / "model_config.yaml"),
        model_filename: file_info(checkpoint_dir / model_filename),
        "lit_model.pth": file_info(checkpoint_dir / "lit_model.pth"),
        "lit_model.pth.lora": file_info(checkpoint_dir / "lit_model.pth.lora"),
        "tokenizer_config.json": file_info(checkpoint_dir / "tokenizer_config.json"),
        "generation_config.json": file_info(checkpoint_dir / "generation_config.json"),
        "config.json": file_info(checkpoint_dir / "config.json"),
        "hyperparameters.yaml": file_info(checkpoint_dir / "hyperparameters.yaml"),
    }
    for name in TOKENIZER_FILE_NAMES:
        files[name] = file_info(checkpoint_dir / name)

    weights = collect_weight_files(checkpoint_dir) if is_dir else {k: [] for k in ("litgpt", "lora", "hf_bin", "hf_safetensors", "hf_index")}
    has_config = files["model_config.yaml"].get("exists", False)
    has_tokenizer_vocab = any(files[name].get("exists", False) for name in TOKENIZER_FILE_NAMES)
    has_tokenizer_config = files["tokenizer_config.json"].get("exists", False)
    has_tokenizer = has_tokenizer_vocab and has_tokenizer_config
    kind = classify(checkpoint_dir, weights, has_config, has_tokenizer_vocab)

    config_summary: dict[str, Any] = {}
    metadata_errors: list[str] = []
    config_data, config_error = parse_metadata(checkpoint_dir / "model_config.yaml")
    if config_error:
        metadata_errors.append(f"model_config.yaml: {config_error}")
    if config_data:
        for key in ("name", "n_layer", "n_embd", "n_head", "vocab_size", "block_size", "mlp_class_name"):
            if key in config_data:
                config_summary[key] = config_data[key]

    issues: list[str] = []
    warnings: list[str] = []
    next_steps: list[str] = []

    if not exists:
        issues.append("checkpoint_dir not found")
    elif not is_dir:
        issues.append("checkpoint_dir is not a directory")

    if is_dir:
        if mode in {"inference", "training", "validate", "litgpt"}:
            if not has_config:
                issues.append("missing model_config.yaml")
            if not has_tokenizer_vocab:
                issues.append("missing tokenizer.json or tokenizer.model")
            if not has_tokenizer_config:
                issues.append("missing tokenizer_config.json")
            if not (checkpoint_dir / model_filename).is_file():
                issues.append(f"missing {model_filename}")
        elif mode == "lora":
            if not has_config:
                issues.append("missing model_config.yaml")
            if not has_tokenizer_vocab:
                issues.append("missing tokenizer.json or tokenizer.model")
            if not has_tokenizer_config:
                issues.append("missing tokenizer_config.json")
            if not (checkpoint_dir / "lit_model.pth.lora").is_file():
                issues.append("missing lit_model.pth.lora")
            if not (checkpoint_dir / "hyperparameters.yaml").is_file():
                issues.append("missing hyperparameters.yaml")
        elif mode == "hf":
            if not (weights["hf_bin"] or weights["hf_safetensors"] or weights["hf_index"]):
                issues.append("missing Hugging Face .bin/.safetensors weight files")
            if not has_tokenizer_vocab:
                warnings.append("missing tokenizer.json or tokenizer.model")
            if not has_tokenizer_config:
                warnings.append("missing tokenizer_config.json")

        if kind == "huggingface-needs-conversion":
            next_steps.append("run litgpt convert_to_litgpt CHECKPOINT_DIR --model_name SUPPORTED_CONFIG_NAME")
        elif kind == "litgpt-ready":
            next_steps.append("run litgpt validate CHECKPOINT_DIR before use")
        elif kind == "litgpt-lora":
            next_steps.append("run scripts/check_lora_metadata.py CHECKPOINT_DIR before litgpt merge_lora")
        elif kind == "tokenizer-only":
            next_steps.append("use for tokenizer-only workflows or download/convert model weights before inference")
        elif kind in {"unknown-or-incomplete", "config-only-or-incomplete"}:
            next_steps.append("locate the checkpoint leaf directory or restore missing LitGPT/HF files")

        if weights["hf_bin"] or weights["hf_safetensors"]:
            if weights["litgpt"]:
                warnings.append("directory contains both HF weights and lit_model.pth; confirm which format downstream expects")
        if weights["lora"] and not files["hyperparameters.yaml"].get("exists", False):
            issues.append("LoRA adapter file exists but hyperparameters.yaml is missing")

    status = "ok" if not issues else "fail"
    return {
        "status": status,
        "classification": kind,
        "mode": mode,
        "path": str(checkpoint_dir),
        "files": files,
        "weight_files": weights,
        "tokenizer": {
            "has_tokenizer_vocab": has_tokenizer_vocab,
            "has_tokenizer_config": has_tokenizer_config,
            "ready": has_tokenizer,
        },
        "config_summary": config_summary,
        "metadata_errors": metadata_errors,
        "issues": issues,
        "warnings": warnings,
        "next_steps": next_steps,
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"classification: {report['classification']}")
    print(f"path: {report['path']}")
    if report["config_summary"]:
        print("config:")
        for key, value in report["config_summary"].items():
            print(f"  {key}: {value}")
    print("weight files:")
    for key, values in report["weight_files"].items():
        print(f"  {key}: {', '.join(values) if values else '-'}")
    print("tokenizer:")
    for key, value in report["tokenizer"].items():
        print(f"  {key}: {value}")
    if report["issues"]:
        print("issues:")
        for issue in report["issues"]:
            print(f"  - {issue}")
    if report["warnings"]:
        print("warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    if report["next_steps"]:
        print("next steps:")
        for step in report["next_steps"]:
            print(f"  - {step}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect LitGPT/Hugging Face checkpoint directory layout.")
    parser.add_argument("checkpoint_dir", type=Path, help="Checkpoint directory to inspect.")
    parser.add_argument(
        "--mode",
        choices=("auto", "litgpt", "validate", "inference", "training", "hf", "lora"),
        default="auto",
        help="Required layout profile to enforce. Default only classifies and reports obvious issues.",
    )
    parser.add_argument(
        "--model-filename",
        default="lit_model.pth",
        help="LitGPT model filename required for validation/inference/training modes.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = build_report(args.checkpoint_dir, args.mode, args.model_filename)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
