#!/usr/bin/env python3
"""Inspect a verl checkpoint path without importing verl or loading tensors."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

STEP_RE = re.compile(r"^global_steps?_(\d+)$")
FSDP_MODEL_RE = re.compile(r"^model_world_size_(\d+)_rank_(\d+)\.pt$")
FSDP_OPTIM_RE = re.compile(r"^optim_world_size_(\d+)_rank_(\d+)\.pt$")
HF_WEIGHT_SUFFIXES = (".safetensors", ".bin")
ROLE_NAMES = {"actor", "critic", "ref", "rollout", "reward", "reward_model"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a verl checkpoint/run/role path by directory layout only. "
            "The script does not import torch/verl and does not load tensor files."
        )
    )
    parser.add_argument("path", type=Path, help="Checkpoint run root, global_step directory, role directory, or HF tree")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--max-children",
        type=int,
        default=80,
        help="Maximum child names to include per inspected directory (default: 80)",
    )
    return parser.parse_args()


def list_child_names(path: Path, max_children: int) -> list[str]:
    try:
        names = sorted(child.name for child in path.iterdir())
    except OSError:
        return []
    if len(names) > max_children:
        return names[:max_children] + [f"... ({len(names) - max_children} more)"]
    return names


def is_hf_tree(path: Path) -> bool:
    if not path.is_dir():
        return False
    names = {child.name for child in safe_iterdir(path)}
    has_config = "config.json" in names
    has_tokenizer = any(name.startswith("tokenizer") or name in {"vocab.json", "merges.txt"} for name in names)
    has_weights = any(name.endswith(HF_WEIGHT_SUFFIXES) for name in names)
    has_index = any(name.endswith(".index.json") for name in names)
    return has_config and (has_tokenizer or has_weights or has_index)


def safe_iterdir(path: Path) -> list[Path]:
    try:
        return list(path.iterdir())
    except OSError:
        return []


def read_tracker(path: Path) -> dict[str, Any] | None:
    tracker = path / "latest_checkpointed_iteration.txt"
    if not tracker.is_file():
        return None
    try:
        text = tracker.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        text = tracker.read_text(errors="replace").strip()
    except OSError as exc:
        return {"path": tracker.name, "error": str(exc)}
    step_text = text.splitlines()[0].strip() if text else ""
    step_dir_candidates = [f"global_step_{step_text}", f"global_steps_{step_text}"] if step_text.isdigit() else []
    return {
        "path": tracker.name,
        "value": step_text,
        "existing_step_dirs": [name for name in step_dir_candidates if (path / name).is_dir()],
    }


def read_json_metadata(path: Path) -> dict[str, Any] | None:
    metadata_path = path / "checkpoint_contents_metadata.json"
    if not metadata_path.is_file():
        return None
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {"path": metadata_path.name, "error": str(exc)}
    summary: dict[str, Any] = {"path": metadata_path.name}
    for key in ("global_step", "layout_version"):
        if key in data:
            summary[key] = data[key]
    backend = data.get("backend")
    if isinstance(backend, dict):
        summary["backend"] = {key: backend.get(key) for key in sorted(backend)}
    contents = data.get("contents")
    if isinstance(contents, dict):
        summary["contents"] = {
            key: value.get("path") if isinstance(value, dict) else value for key, value in sorted(contents.items())
        }
    return summary


def classify_path(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "input": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "kind": "missing",
        "likely_backend": "unknown",
        "warnings": [],
        "suggestions": [],
    }
    if not path.exists():
        result["warnings"].append("Path does not exist.")
        return result
    if not path.is_dir():
        result["kind"] = "file"
        result["warnings"].append("Expected a directory path.")
        return result

    children = safe_iterdir(path)
    child_names = {child.name for child in children}
    result["child_names"] = sorted(child_names)[:80]

    step_children = sorted(child.name for child in children if child.is_dir() and STEP_RE.match(child.name))
    role_children = sorted(child.name for child in children if child.is_dir() and child.name in ROLE_NAMES)
    tracker = read_tracker(path)
    metadata = read_json_metadata(path)

    if tracker:
        result["latest_tracker"] = tracker
    if metadata:
        result["megatron_metadata"] = metadata

    fsdp_model_shards = sorted(name for name in child_names if FSDP_MODEL_RE.match(name))
    fsdp_optim_shards = sorted(name for name in child_names if FSDP_OPTIM_RE.match(name))
    has_fsdp_config = "fsdp_config.json" in child_names
    has_top_hf = is_hf_tree(path / "huggingface")
    has_self_hf = is_hf_tree(path)
    has_megatron_model_dist = (path / "model" / "dist_ckpt").is_dir()
    has_megatron_model_hf = is_hf_tree(path / "model" / "huggingface")
    has_megatron_metadata = metadata is not None

    if step_children:
        result["kind"] = "run_root"
        result["step_dirs"] = step_children
        result["suggestions"].append("Choose a global_step directory, then a role directory such as actor, before merging.")
        if tracker and tracker.get("existing_step_dirs"):
            result["suggestions"].append("The latest tracker points to an existing step directory.")
        elif tracker:
            result["warnings"].append("The latest tracker does not point to an existing step directory under this root.")
    elif STEP_RE.match(path.name) or role_children:
        result["kind"] = "step_root"
        result["role_dirs"] = role_children
        if role_children:
            result["suggestions"].append("Use a role directory, usually actor, as verl.model_merger --local_dir.")
        else:
            result["warnings"].append("This looks like a step root but no common role directories were found.")
    elif has_self_hf:
        result["kind"] = "huggingface_tree"
        result["likely_backend"] = "huggingface"
        result["suggestions"].append("This already looks like a HuggingFace-format tree; validate or copy it instead of merging shards.")
    elif has_fsdp_config or fsdp_model_shards:
        result["kind"] = "role_dir"
        result["likely_backend"] = "fsdp"
        result["fsdp"] = {
            "has_fsdp_config": has_fsdp_config,
            "model_shard_count": len(fsdp_model_shards),
            "optimizer_shard_count": len(fsdp_optim_shards),
            "sample_model_shards": fsdp_model_shards[:5],
            "has_huggingface_subdir": (path / "huggingface").is_dir(),
            "huggingface_subdir_looks_complete": has_top_hf,
            "has_lora_train_meta": "lora_train_meta.json" in child_names,
        }
        if not has_fsdp_config:
            result["warnings"].append("FSDP shards found without fsdp_config.json; current merger expects fsdp_config.json.")
        if has_top_hf:
            result["suggestions"].append("A HuggingFace subdirectory looks complete; use it directly if no fresh merge is needed.")
        result["suggestions"].append("For HF export from shards, run verl.model_merger merge with --backend fsdp and this directory as --local_dir.")
    elif has_megatron_metadata or has_megatron_model_dist or has_megatron_model_hf:
        result["kind"] = "role_dir"
        result["likely_backend"] = "megatron"
        result["megatron"] = {
            "has_metadata": has_megatron_metadata,
            "has_model_dist_ckpt": has_megatron_model_dist,
            "has_model_huggingface": (path / "model" / "huggingface").is_dir(),
            "model_huggingface_looks_complete": has_megatron_model_hf,
            "has_optimizer_dist_ckpt": (path / "optimizer" / "dist_ckpt").is_dir(),
            "has_extra_dist_ckpt": (path / "extra" / "dist_ckpt").is_dir(),
            "has_transformer_config": "transformer_config.json" in child_names,
        }
        if not has_megatron_metadata:
            result["warnings"].append("Megatron-like layout found without checkpoint_contents_metadata.json; it may be old or incomplete.")
        if has_megatron_model_hf:
            result["suggestions"].append("model/huggingface looks complete; use it directly if a deployable HF export was already saved.")
        if has_megatron_model_dist:
            result["suggestions"].append("For HF export from Megatron shards, run verl.model_merger merge with --backend megatron and this directory as --local_dir.")
    else:
        result["kind"] = "directory"
        result["warnings"].append("Directory does not match common verl run, step, role, FSDP, Megatron, or HuggingFace layouts.")

    if "lora_train_meta.json" in child_names:
        result["suggestions"].append("LoRA metadata is present; confirm whether the desired export should merge adapter weights.")

    return result


def main() -> int:
    args = parse_args()
    result = classify_path(args.path)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result.get("exists") else 2


if __name__ == "__main__":
    raise SystemExit(main())
