#!/usr/bin/env python3
"""Non-destructive ControlNet checkpoint key-mapping inspector.

This script adapts the key-mapping logic from the ControlNet 1.0 add-control
utilities, but it never saves checkpoints, downloads weights, trains, or runs
image generation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


CONFIG_BY_FAMILY = {
    "sd15": "models/cldm_v15.yaml",
    "sd21": "models/cldm_v21.yaml",
}


def get_node_name(name: str, parent_name: str) -> tuple[bool, str]:
    if len(name) <= len(parent_name):
        return False, ""
    prefix = name[: len(parent_name)]
    if prefix != parent_name:
        return False, ""
    return True, name[len(parent_name) :]


def source_key_for_target(target_key: str) -> tuple[str, bool]:
    is_control, suffix = get_node_name(target_key, "control_")
    if is_control:
        return "model.diffusion_" + suffix, True
    return target_key, False


def unwrap_state_dict(obj: Any) -> Any:
    if isinstance(obj, dict) and "state_dict" in obj:
        return obj["state_dict"]
    return obj


def load_key_list(path: Path) -> tuple[set[str], dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    keys: Iterable[str]
    shapes: dict[str, str] = {}
    if stripped.startswith("{") or stripped.startswith("["):
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            keys = parsed.keys()
            for key, value in parsed.items():
                if isinstance(value, (list, tuple)):
                    shapes[str(key)] = "x".join(str(v) for v in value)
                elif isinstance(value, str):
                    shapes[str(key)] = value
        elif isinstance(parsed, list):
            keys = parsed
        else:
            raise ValueError(f"Unsupported JSON key-list format in {path}")
    else:
        keys = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return {str(key) for key in keys}, shapes


def load_checkpoint_keys(path: Path, location: str) -> tuple[set[str], dict[str, str]]:
    extension = path.suffix.lower()
    if extension == ".safetensors":
        try:
            import safetensors.torch  # type: ignore
        except ImportError as exc:
            raise RuntimeError("safetensors is required to inspect .safetensors files") from exc
        state_dict = safetensors.torch.load_file(str(path), device=location)
    else:
        try:
            import torch  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PyTorch is required to inspect PyTorch checkpoint files") from exc
        state_dict = torch.load(str(path), map_location=torch.device(location))
    state_dict = unwrap_state_dict(unwrap_state_dict(state_dict))
    if not hasattr(state_dict, "keys"):
        raise RuntimeError(f"Checkpoint did not resolve to a state-dict-like object: {path}")
    shapes = {}
    for key, value in state_dict.items():
        if hasattr(value, "shape"):
            shapes[str(key)] = "x".join(str(dim) for dim in value.shape)
    return {str(key) for key in state_dict.keys()}, shapes


def fallback_yaml_summary(config_path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {"config_path": str(config_path), "parser": "line-scan"}
    lines = config_path.read_text(encoding="utf-8").splitlines()
    target_hits: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("target:"):
            target_hits.append(stripped.split("target:", 1)[1].strip().strip('"\''))
        elif stripped.startswith("context_dim:"):
            summary.setdefault("context_dim", stripped.split(":", 1)[1].strip())
        elif stripped.startswith("num_heads:"):
            summary.setdefault("num_heads", stripped.split(":", 1)[1].strip())
        elif stripped.startswith("num_head_channels:"):
            summary.setdefault("num_head_channels", stripped.split(":", 1)[1].strip())
        elif stripped.startswith("use_linear_in_transformer:"):
            summary.setdefault("use_linear_in_transformer", stripped.split(":", 1)[1].strip())
    if target_hits:
        summary["targets"] = target_hits
        summary["model_target"] = target_hits[0]
    return summary


def nested_get(mapping: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = mapping
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def summarize_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {"config_path": str(config_path), "error": "config file not found"}
    try:
        import yaml  # type: ignore
    except ImportError:
        return fallback_yaml_summary(config_path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    model = nested_get(data, ["model"], {}) or {}
    params = model.get("params", {}) if isinstance(model, dict) else {}
    control_params = nested_get(params, ["control_stage_config", "params"], {}) or {}
    unet_params = nested_get(params, ["unet_config", "params"], {}) or {}
    return {
        "config_path": str(config_path),
        "parser": "pyyaml",
        "model_target": model.get("target") if isinstance(model, dict) else None,
        "control_target": nested_get(params, ["control_stage_config", "target"]),
        "unet_target": nested_get(params, ["unet_config", "target"]),
        "cond_stage_target": nested_get(params, ["cond_stage_config", "target"]),
        "first_stage_key": params.get("first_stage_key"),
        "cond_stage_key": params.get("cond_stage_key"),
        "control_key": params.get("control_key"),
        "control_context_dim": control_params.get("context_dim"),
        "unet_context_dim": unet_params.get("context_dim"),
        "control_num_heads": control_params.get("num_heads"),
        "control_num_head_channels": control_params.get("num_head_channels"),
        "control_use_linear_in_transformer": control_params.get("use_linear_in_transformer"),
        "unet_use_linear_in_transformer": unet_params.get("use_linear_in_transformer"),
    }


def instantiate_scratch_keys(repo_root: Path, config_path: Path) -> tuple[set[str], dict[str, str]]:
    sys.path.insert(0, str(repo_root))
    from cldm.model import create_model  # type: ignore

    model = create_model(str(config_path))
    state_dict = model.state_dict()
    shapes = {}
    for key, value in state_dict.items():
        if hasattr(value, "shape"):
            shapes[str(key)] = "x".join(str(dim) for dim in value.shape)
    return {str(key) for key in state_dict.keys()}, shapes


def inspect_mapping(scratch_keys: set[str], source_keys: set[str]) -> dict[str, Any]:
    mapped: list[dict[str, Any]] = []
    newly_initialized: list[dict[str, Any]] = []
    control_total = 0
    control_mapped = 0
    for target_key in sorted(scratch_keys):
        source_key, is_control = source_key_for_target(target_key)
        if is_control:
            control_total += 1
        item = {"target_key": target_key, "source_key": source_key, "is_control_key": is_control}
        if source_key in source_keys:
            mapped.append(item)
            if is_control:
                control_mapped += 1
        else:
            newly_initialized.append(item)
    return {
        "total_scratch_keys": len(scratch_keys),
        "total_source_keys": len(source_keys),
        "mapped_count": len(mapped),
        "newly_initialized_count": len(newly_initialized),
        "control_key_count": control_total,
        "control_mapped_count": control_mapped,
        "control_newly_initialized_count": control_total - control_mapped,
        "mapped": mapped,
        "newly_initialized": newly_initialized,
    }


def self_test(max_rows: int) -> dict[str, Any]:
    scratch_keys = {
        "model.diffusion_model.input_blocks.0.0.weight",
        "control_model.input_blocks.0.0.weight",
        "control_model.zero_convs.0.0.weight",
        "first_stage_model.encoder.conv_in.weight",
    }
    source_keys = {
        "model.diffusion_model.input_blocks.0.0.weight",
        "first_stage_model.encoder.conv_in.weight",
    }
    report = inspect_mapping(scratch_keys, source_keys)
    newly = {item["target_key"] for item in report["newly_initialized"]}
    mapped = {item["target_key"] for item in report["mapped"]}
    assert "control_model.input_blocks.0.0.weight" in mapped
    assert "control_model.zero_convs.0.0.weight" in newly
    assert report["mapped_count"] == 3
    assert report["newly_initialized_count"] == 1
    return {
        "self_test": "passed",
        "note": "fake state-dict keys validate the control_ -> model.diffusion_ mapping rule",
        "mapping_report": limit_report(report, max_rows),
    }


def limit_report(report: dict[str, Any], max_rows: int) -> dict[str, Any]:
    limited = dict(report)
    limited["mapped"] = report.get("mapped", [])[:max_rows]
    limited["newly_initialized"] = report.get("newly_initialized", [])[:max_rows]
    return limited


def print_human(result: dict[str, Any]) -> None:
    print("ControlNet weight mapping dry run")
    print("=================================")
    if "self_test" in result:
        print(f"self_test: {result['self_test']}")
        print(result.get("note", ""))
        result = result["mapping_report"]
    config = result.get("config")
    if config:
        print("\nConfig summary:")
        for key, value in config.items():
            if value is not None:
                print(f"  {key}: {value}")
    if result.get("scratch_key_source"):
        print(f"\nScratch key source: {result['scratch_key_source']}")
    if result.get("source_key_source"):
        print(f"Source key source: {result['source_key_source']}")
    if result.get("scratch_key_error"):
        print(f"Scratch key error: {result['scratch_key_error']}")
    if result.get("source_key_error"):
        print(f"Source key error: {result['source_key_error']}")
    if "mapped_count" not in result:
        print("\nMapping report unavailable: provide scratch keys/model instantiation and source checkpoint keys.")
        return
    print("\nMapping summary:")
    summary_keys = [
        "total_scratch_keys",
        "total_source_keys",
        "mapped_count",
        "newly_initialized_count",
        "control_key_count",
        "control_mapped_count",
        "control_newly_initialized_count",
    ]
    for key in summary_keys:
        print(f"  {key}: {result[key]}")
    print("\nMapped examples:")
    for item in result.get("mapped", []):
        print(f"  {item['target_key']}  <=  {item['source_key']}")
    if not result.get("mapped"):
        print("  none")
    print("\nNewly initialized examples:")
    for item in result.get("newly_initialized", []):
        print(f"  {item['target_key']}  (missing source: {item['source_key']})")
    if not result.get("newly_initialized"):
        print("  none")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run ControlNet add-control state-dict mapping. The script reports "
            "which scratch ControlNet keys would copy from a base Stable Diffusion "
            "checkpoint and which would stay newly initialized. It never saves outputs."
        )
    )
    parser.add_argument("--repo-root", default=".", help="ControlNet source checkout used for config/model inspection.")
    parser.add_argument("--config-family", choices=sorted(CONFIG_BY_FAMILY), default="sd15", help="Built-in config family to inspect.")
    parser.add_argument("--config-path", help="Explicit config YAML path; overrides --config-family lookup.")
    parser.add_argument("--checkpoint", help="Optional base SD checkpoint to inspect (.ckpt/.pth/.safetensors).")
    parser.add_argument("--checkpoint-key-list", help="Optional text or JSON file of source checkpoint keys; avoids loading checkpoint tensors.")
    parser.add_argument("--scratch-key-list", help="Optional text or JSON file of scratch ControlNet model keys; avoids model instantiation.")
    parser.add_argument("--no-instantiate-model", action="store_true", help="Do not instantiate create_model when scratch keys are not provided.")
    parser.add_argument("--location", default="cpu", help="Device for optional checkpoint loading; default: cpu.")
    parser.add_argument("--max-rows", type=int, default=40, help="Maximum mapped/new key examples to print or include.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    parser.add_argument("--self-test", action="store_true", help="Run a tiny fake-state-dict self-test and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    max_rows = max(args.max_rows, 0)

    if args.self_test:
        result = self_test(max_rows)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print_human(result)
        return 0

    repo_root = Path(args.repo_root).expanduser().resolve()
    config_path = Path(args.config_path).expanduser() if args.config_path else repo_root / CONFIG_BY_FAMILY[args.config_family]
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()

    result: dict[str, Any] = {"config": summarize_config(config_path)}

    scratch_keys: set[str] | None = None
    source_keys: set[str] | None = None

    if args.scratch_key_list:
        scratch_path = Path(args.scratch_key_list).expanduser()
        scratch_keys, _ = load_key_list(scratch_path)
        result["scratch_key_source"] = f"key-list:{scratch_path}"
    elif not args.no_instantiate_model:
        try:
            scratch_keys, _ = instantiate_scratch_keys(repo_root, config_path)
            result["scratch_key_source"] = f"create_model:{config_path.name}"
        except Exception as exc:  # noqa: BLE001 - diagnostic tool should report and continue
            result["scratch_key_error"] = f"{type(exc).__name__}: {exc}"

    if args.checkpoint_key_list:
        source_path = Path(args.checkpoint_key_list).expanduser()
        source_keys, _ = load_key_list(source_path)
        result["source_key_source"] = f"key-list:{source_path}"
    elif args.checkpoint:
        checkpoint_path = Path(args.checkpoint).expanduser()
        try:
            source_keys, _ = load_checkpoint_keys(checkpoint_path, args.location)
            result["source_key_source"] = f"checkpoint:{checkpoint_path}"
        except Exception as exc:  # noqa: BLE001 - diagnostic tool should report and continue
            result["source_key_error"] = f"{type(exc).__name__}: {exc}"

    if scratch_keys is not None and source_keys is not None:
        result.update(limit_report(inspect_mapping(scratch_keys, source_keys), max_rows))
    else:
        if scratch_keys is not None:
            result["total_scratch_keys"] = len(scratch_keys)
        if source_keys is not None:
            result["total_source_keys"] = len(source_keys)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
