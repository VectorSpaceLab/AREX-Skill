#!/usr/bin/env python3
"""Inspect a JSON-with-comments config for the SR3/DDPM iterative-refinement repo.

This helper is safe by default: it parses and summarizes a config but does not
create experiment directories, import torch, load checkpoints, or launch a run.

Examples:
    python scripts/inspect_config.py /path/to/checkout/config/sr_sr3_16_128.json
    python scripts/inspect_config.py /path/to/checkout/config/sample_sr3_128.json --check-paths --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable


def strip_json_comments(text: str) -> str:
    """Mimic the repository parser: keep text before // on each line."""
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def load_jsonc(path: Path) -> OrderedDict[str, Any]:
    try:
        return json.loads(strip_json_comments(path.read_text()), object_pairs_hook=OrderedDict)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: could not parse {path}: {exc}") from exc


def nested(mapping: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    cur: Any = mapping
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def rel_or_abs(path_value: str | None, repo_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return repo_root / path


def summarize(config: dict[str, Any]) -> list[str]:
    model = config.get("model", {})
    unet = model.get("unet", {})
    diffusion = model.get("diffusion", {})
    train = config.get("train", {})
    lines = [
        f"name: {config.get('name')}",
        f"declared phase: {config.get('phase')}",
        f"gpu_ids: {config.get('gpu_ids')}",
        f"model.which_model_G: {model.get('which_model_G')}",
        f"model.diffusion.conditional: {diffusion.get('conditional')}",
        f"model.diffusion.image_size: {diffusion.get('image_size')}",
        f"unet in/out: {unet.get('in_channel')} -> {unet.get('out_channel')}",
        f"unet inner_channel: {unet.get('inner_channel')}",
        f"unet channel_multiplier: {unet.get('channel_multiplier')}",
        f"unet attn_res: {unet.get('attn_res')}",
        f"train.n_iter: {train.get('n_iter')}",
        f"train.val_freq: {train.get('val_freq')}",
        f"train.save_checkpoint_freq: {train.get('save_checkpoint_freq')}",
        f"path.resume_state: {nested(config, ['path', 'resume_state'])}",
    ]
    for schedule_phase in ("train", "val"):
        sched = nested(model, ["beta_schedule", schedule_phase], {}) or {}
        lines.append(
            f"beta_schedule.{schedule_phase}: {sched.get('schedule')} "
            f"n={sched.get('n_timestep')} start={sched.get('linear_start')} end={sched.get('linear_end')}"
        )
    for phase, ds in (config.get("datasets", {}) or {}).items():
        lines.append(
            f"dataset.{phase}: mode={ds.get('mode')} datatype={ds.get('datatype')} "
            f"root={ds.get('dataroot')} L={ds.get('l_resolution')} R={ds.get('r_resolution')} "
            f"data_len={ds.get('data_len')} batch={ds.get('batch_size')} workers={ds.get('num_workers')}"
        )
    return lines


def validate_invariants(config: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    conditional = nested(config, ["model", "diffusion", "conditional"])
    in_channel = nested(config, ["model", "unet", "in_channel"])
    out_channel = nested(config, ["model", "unet", "out_channel"])
    if conditional is True and in_channel != 6:
        warnings.append("conditional SR config usually needs unet.in_channel == 6")
    if conditional is False and in_channel != 3:
        warnings.append("unconditional sample config usually needs unet.in_channel == 3")
    if out_channel != 3:
        warnings.append("image RGB workflows normally use unet.out_channel == 3")
    gpu_ids = config.get("gpu_ids")
    if gpu_ids is None:
        warnings.append("gpu_ids is null; stock parser behavior may not support CPU-only configs without adaptation")
    resume_state = nested(config, ["path", "resume_state"])
    if isinstance(resume_state, str) and resume_state.endswith(("_gen.pth", "_opt.pth")):
        warnings.append("path.resume_state should be a checkpoint stem, not a suffixed .pth file")
    return warnings


def check_paths(config: dict[str, Any], repo_root: Path, phase: str | None) -> list[str]:
    messages: list[str] = []
    datasets = config.get("datasets", {}) or {}
    selected_phases = [phase] if phase else sorted(datasets)
    for ds_phase in selected_phases:
        ds = datasets.get(ds_phase)
        if not ds:
            messages.append(f"WARN: no datasets.{ds_phase} section")
            continue
        root = rel_or_abs(ds.get("dataroot"), repo_root)
        if root is None:
            messages.append(f"WARN: datasets.{ds_phase}.dataroot is empty")
        elif root.exists():
            messages.append(f"OK: datasets.{ds_phase}.dataroot exists: {root}")
        else:
            messages.append(f"WARN: datasets.{ds_phase}.dataroot does not exist: {root}")
    stem = nested(config, ["path", "resume_state"])
    if stem:
        gen = rel_or_abs(f"{stem}_gen.pth", repo_root)
        opt = rel_or_abs(f"{stem}_opt.pth", repo_root)
        messages.append(("OK" if gen and gen.exists() else "WARN") + f": generator checkpoint {gen}")
        messages.append(("OK" if opt and opt.exists() else "WARN") + f": optimizer checkpoint {opt}")
    return messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize and lightly validate an SR3/DDPM JSON-with-comments config.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("config", type=Path, help="Path to a comment-bearing JSON config.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Checkout root for optional path checks.")
    parser.add_argument("--phase", choices=["train", "val"], help="Dataset phase to check when --check-paths is set.")
    parser.add_argument("--check-paths", action="store_true", help="Check dataset/checkpoint path existence without running workflows.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable summary instead of text.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_jsonc(args.config)
    summary = summarize(config)
    warnings = validate_invariants(config)
    path_messages = check_paths(config, args.repo_root, args.phase) if args.check_paths else []
    if args.json:
        print(json.dumps({"summary": summary, "warnings": warnings, "path_messages": path_messages}, indent=2))
    else:
        print("# Config summary")
        for line in summary:
            print(line)
        if warnings:
            print("\n# Warnings")
            for item in warnings:
                print(f"WARN: {item}")
        if path_messages:
            print("\n# Path checks")
            for item in path_messages:
                print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
