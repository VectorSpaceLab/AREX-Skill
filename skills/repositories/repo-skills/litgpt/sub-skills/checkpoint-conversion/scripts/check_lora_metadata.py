#!/usr/bin/env python3
"""Safely inspect LitGPT LoRA checkpoint metadata.

This checker reads hyperparameters.yaml and file presence only. It never loads
base weights, LoRA weights, or writes merged checkpoints.
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


EXPECTED_LORA_KEYS = (
    "lora_r",
    "lora_alpha",
    "lora_dropout",
    "lora_query",
    "lora_key",
    "lora_value",
    "lora_projection",
    "lora_mlp",
    "lora_head",
)


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
        if yaml is None:
            data = parse_simple_yaml_mapping(text)
        else:
            data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report parse errors
        return None, str(exc)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "hyperparameters.yaml must contain a mapping"
    return data, None


def file_state(path: Path) -> dict[str, Any]:
    return {
        "exists": path.exists(),
        "is_file": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
    }


def build_report(checkpoint_dir: Path, base_checkpoint_dir: Path | None = None) -> dict[str, Any]:
    checkpoint_dir = checkpoint_dir.expanduser()
    hparams_path = checkpoint_dir / "hyperparameters.yaml"
    issues: list[str] = []
    warnings: list[str] = []
    next_steps: list[str] = []

    if not checkpoint_dir.exists():
        issues.append("checkpoint_dir not found")
    elif not checkpoint_dir.is_dir():
        issues.append("checkpoint_dir is not a directory")

    files = {
        "model_config.yaml": file_state(checkpoint_dir / "model_config.yaml"),
        "lit_model.pth.lora": file_state(checkpoint_dir / "lit_model.pth.lora"),
        "lit_model.pth": file_state(checkpoint_dir / "lit_model.pth"),
        "hyperparameters.yaml": file_state(hparams_path),
        "tokenizer.json": file_state(checkpoint_dir / "tokenizer.json"),
        "tokenizer.model": file_state(checkpoint_dir / "tokenizer.model"),
        "tokenizer_config.json": file_state(checkpoint_dir / "tokenizer_config.json"),
    }

    if checkpoint_dir.is_dir():
        if not files["model_config.yaml"]["is_file"]:
            issues.append("missing model_config.yaml")
        if not files["lit_model.pth.lora"]["is_file"]:
            issues.append("missing lit_model.pth.lora")
        if not (files["tokenizer.json"]["is_file"] or files["tokenizer.model"]["is_file"]):
            warnings.append("missing tokenizer.json or tokenizer.model")
        if not files["tokenizer_config.json"]["is_file"]:
            warnings.append("missing tokenizer_config.json")
        if files["lit_model.pth"]["is_file"]:
            warnings.append("lit_model.pth already exists; LoRA weights may already be merged")

    hparams: dict[str, Any] = {}
    parse_error = None
    if not hparams_path.is_file():
        issues.append("missing hyperparameters.yaml")
    else:
        hparams, parse_error = load_yaml(hparams_path)
        if parse_error:
            issues.append(f"cannot parse hyperparameters.yaml: {parse_error}")
            hparams = {}

    lora_params = {key: hparams[key] for key in sorted(hparams) if key.startswith("lora_")}
    missing_core_keys = [key for key in ("lora_r", "lora_alpha") if key not in hparams]
    missing_common_keys = [key for key in EXPECTED_LORA_KEYS if key not in hparams]
    checkpoint_dir_value = hparams.get("checkpoint_dir")
    precision = hparams.get("precision")

    if hparams_path.is_file() and not parse_error:
        if not checkpoint_dir_value:
            issues.append("hyperparameters.yaml missing checkpoint_dir")
        if not lora_params:
            issues.append("hyperparameters.yaml has no lora_* keys")
        elif missing_core_keys:
            issues.append("hyperparameters.yaml missing core LoRA keys: " + ", ".join(missing_core_keys))
        if missing_common_keys:
            warnings.append("hyperparameters.yaml missing common LoRA keys: " + ", ".join(missing_common_keys))
        if precision is None:
            warnings.append("precision is not recorded; merge_lora will rely on default/explicit precision")

    metadata_base_path = Path(str(checkpoint_dir_value)).expanduser() if checkpoint_dir_value else None
    effective_base_path = base_checkpoint_dir.expanduser() if base_checkpoint_dir else metadata_base_path
    base_state: dict[str, Any] | None = None
    if effective_base_path is not None:
        base_state = {
            "path": str(effective_base_path),
            "exists": effective_base_path.exists(),
            "is_dir": effective_base_path.is_dir(),
            "has_lit_model": (effective_base_path / "lit_model.pth").is_file(),
            "has_model_config": (effective_base_path / "model_config.yaml").is_file(),
        }
        if not effective_base_path.exists():
            warnings.append("base checkpoint path does not exist from this environment")
        elif not effective_base_path.is_dir():
            issues.append("base checkpoint path is not a directory")
        else:
            if not base_state["has_lit_model"]:
                issues.append("base checkpoint missing lit_model.pth")
            if not base_state["has_model_config"]:
                issues.append("base checkpoint missing model_config.yaml")

    if "missing hyperparameters.yaml" in issues:
        next_steps.append("recover hyperparameters.yaml from the LoRA training command, recipe, or logs before merging")
        next_steps.append("when only the base path moved, pass --pretrained_checkpoint_dir BASE_CHECKPOINT_DIR to litgpt merge_lora")
    elif issues:
        next_steps.append("fix required metadata/files before running litgpt merge_lora")
    else:
        command = f"litgpt merge_lora {checkpoint_dir}"
        if base_checkpoint_dir is not None:
            command += f" --pretrained_checkpoint_dir {base_checkpoint_dir}"
        next_steps.append(command)

    status = "ok" if not issues else "fail"
    return {
        "status": status,
        "path": str(checkpoint_dir),
        "files": files,
        "lora_params": lora_params,
        "missing_common_lora_keys": missing_common_keys,
        "metadata_checkpoint_dir": str(metadata_base_path) if metadata_base_path is not None else None,
        "effective_base_checkpoint_dir": str(effective_base_path) if effective_base_path is not None else None,
        "base_checkpoint": base_state,
        "precision": precision,
        "issues": issues,
        "warnings": warnings,
        "next_steps": next_steps,
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"path: {report['path']}")
    print("files:")
    for name, state in report["files"].items():
        marker = "yes" if state["is_file"] else "no"
        print(f"  {name}: {marker}")
    print("lora params:")
    if report["lora_params"]:
        for key, value in report["lora_params"].items():
            print(f"  {key}: {value}")
    else:
        print("  -")
    print(f"metadata checkpoint_dir: {report['metadata_checkpoint_dir'] or '-'}")
    print(f"effective base checkpoint_dir: {report['effective_base_checkpoint_dir'] or '-'}")
    print(f"precision: {report['precision'] or '-'}")
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
    parser = argparse.ArgumentParser(description="Safely inspect LitGPT LoRA metadata without loading weights.")
    parser.add_argument("checkpoint_dir", type=Path, help="LoRA checkpoint directory to inspect.")
    parser.add_argument(
        "--pretrained-checkpoint-dir",
        type=Path,
        help="Optional base checkpoint directory to validate instead of metadata checkpoint_dir.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = build_report(args.checkpoint_dir, args.pretrained_checkpoint_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
