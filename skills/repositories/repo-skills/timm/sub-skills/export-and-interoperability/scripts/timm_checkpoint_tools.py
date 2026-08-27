#!/usr/bin/env python3
"""Safe helpers for timm checkpoint inspection and command construction."""

import argparse
import glob
import hashlib
import json
import os
import shlex
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence


def _quote(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _require_missing(path: Path) -> None:
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {path}")


def _sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_checkpoint(path: Path, weights_only: bool) -> object:
    try:
        import torch
    except ImportError as error:
        raise SystemExit("Inspecting checkpoint contents requires torch to be installed.") from error

    load_kwargs = {"map_location": "cpu"}
    try:
        return torch.load(path, weights_only=weights_only, **load_kwargs)
    except TypeError:
        if weights_only:
            raise SystemExit("This torch version does not support weights_only=True; rerun with --unsafe-load if trusted.")
        return torch.load(path, **load_kwargs)
    except Exception as error:
        if weights_only:
            raise SystemExit(
                "Safe checkpoint load failed. If and only if this file is trusted, rerun with --unsafe-load. "
                f"Original error: {error}"
            ) from error
        raise


def _state_dict_candidates(checkpoint: object) -> Dict[str, Mapping[str, object]]:
    if isinstance(checkpoint, Mapping):
        candidates = {}
        for key in ("state_dict_ema", "model_ema", "state_dict", "model"):
            value = checkpoint.get(key)
            if isinstance(value, Mapping):
                candidates[key] = value
        if checkpoint and all(hasattr(value, "shape") for value in checkpoint.values()):
            candidates["root"] = checkpoint
        return candidates
    return {}


def inspect_checkpoint(args: argparse.Namespace) -> None:
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.is_file():
        raise SystemExit(f"Checkpoint does not exist: {checkpoint_path}")

    checkpoint = _load_checkpoint(checkpoint_path, weights_only=not args.unsafe_load)
    report = {
        "path": str(checkpoint_path),
        "size_bytes": checkpoint_path.stat().st_size,
        "sha256": _sha256(checkpoint_path) if args.sha256 else None,
        "top_level_type": type(checkpoint).__name__,
        "top_level_keys": [],
        "state_dict_candidates": {},
        "notes": [],
    }

    if isinstance(checkpoint, Mapping):
        report["top_level_keys"] = [str(key) for key in list(checkpoint.keys())[: args.max_keys]]
        if len(checkpoint) > args.max_keys:
            report["notes"].append(f"top_level_keys truncated to {args.max_keys}")

    for name, state_dict in _state_dict_candidates(checkpoint).items():
        keys = [str(key) for key in list(state_dict.keys())]
        prefixed = sum(1 for key in keys if key.startswith("module."))
        aux_bn = sum(1 for key in keys if "aux_bn" in key)
        report["state_dict_candidates"][name] = {
            "num_keys": len(keys),
            "sample_keys": keys[: args.max_keys],
            "module_prefix_keys": prefixed,
            "aux_bn_keys": aux_bn,
        }

    if not report["state_dict_candidates"]:
        report["notes"].append("No obvious state_dict mapping found; checkpoint may need a custom loader.")
    if "state_dict_ema" in report["state_dict_candidates"] or "model_ema" in report["state_dict_candidates"]:
        report["notes"].append("EMA weights appear present; timm cleaning/averaging uses EMA by default unless disabled.")

    print(json.dumps(report, indent=2, sort_keys=True))


def build_clean_command(args: argparse.Namespace) -> List[str]:
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.is_file():
        raise SystemExit(f"Checkpoint does not exist: {checkpoint_path}")
    output_path = Path(args.output)
    _require_missing(output_path)

    command = [args.python, args.script, "--checkpoint", str(checkpoint_path), "--output", str(output_path)]
    if args.no_use_ema:
        command.append("--no-use-ema")
    if args.no_hash:
        command.append("--no-hash")
    if args.clean_aux_bn:
        command.append("--clean-aux-bn")
    if args.safetensors:
        command.append("--safetensors")
    return command


def print_clean_command(args: argparse.Namespace) -> None:
    print(_quote(build_clean_command(args)))


def build_average_command(args: argparse.Namespace) -> List[str]:
    output_path = Path(args.output)
    _require_missing(output_path)
    pattern = os.path.join(args.input, args.filter) if args.input else args.filter
    matches = sorted(glob.glob(pattern, recursive=True))
    if not matches:
        raise SystemExit(f"No checkpoints match pattern: {pattern}")

    command = [
        args.python,
        args.script,
        "--input",
        args.input,
        "--filter",
        args.filter,
        "--output",
        str(output_path),
        "-n",
        str(args.n),
    ]
    if args.no_use_ema:
        command.append("--no-use-ema")
    if args.no_sort:
        command.append("--no-sort")
    if args.safetensors:
        command.append("--safetensors")
    return command


def print_average_command(args: argparse.Namespace) -> None:
    print(_quote(build_average_command(args)))


def average_checkpoints(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    _require_missing(output_path)
    try:
        import torch
        from timm.models import load_state_dict
        try:
            import safetensors.torch
        except ImportError:
            safetensors = None
    except ImportError as error:
        raise SystemExit("Averaging checkpoints requires torch and timm to be installed.") from error

    if args.safetensors and safetensors is None:
        raise SystemExit("Saving safetensors requires `pip install safetensors`.")

    pattern = os.path.join(args.input, args.filter) if args.input else args.filter
    checkpoints = sorted(glob.glob(pattern, recursive=True))
    if args.limit is not None:
        checkpoints = checkpoints[: args.limit]
    if not checkpoints:
        raise SystemExit(f"No checkpoints match pattern: {pattern}")

    avg_state_dict = {}
    avg_counts = {}
    for checkpoint in checkpoints:
        state_dict = load_state_dict(checkpoint, use_ema=not args.no_use_ema)
        for key, value in state_dict.items():
            if not hasattr(value, "to"):
                continue
            if key not in avg_state_dict:
                avg_state_dict[key] = value.clone().to(dtype=torch.float64)
                avg_counts[key] = 1
            else:
                avg_state_dict[key] += value.to(dtype=torch.float64)
                avg_counts[key] += 1

    float32_info = torch.finfo(torch.float32)
    final_state_dict = {}
    for key, value in avg_state_dict.items():
        value.div_(avg_counts[key])
        final_state_dict[key] = value.clamp(float32_info.min, float32_info.max).to(dtype=torch.float32)

    if args.safetensors:
        safetensors.torch.save_file(final_state_dict, output_path)
    else:
        torch.save(final_state_dict, output_path)
    print(json.dumps({"output": str(output_path), "num_inputs": len(checkpoints), "sha256": _sha256(output_path)}, indent=2))


def add_common_command_args(parser: argparse.ArgumentParser, default_script: str) -> None:
    parser.add_argument("--python", default="python", help="Python executable token to print in dry commands.")
    parser.add_argument("--script", default=default_script, help="Script path token to print in dry commands.")


def add_clean_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", required=True, help="Input checkpoint path.")
    parser.add_argument("--output", required=True, help="Output path; existing files are refused.")
    parser.add_argument("--no-use-ema", action="store_true", help="Do not prefer EMA weights.")
    parser.add_argument("--no-hash", action="store_true", help="Do not append SHA256 prefix in clean_checkpoint.py.")
    parser.add_argument("--clean-aux-bn", action="store_true", help="Remove SplitBN auxiliary batch norm keys.")
    parser.add_argument("--safetensors", action="store_true", help="Use safetensors output.")


def add_average_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", required=True, help="Input directory containing checkpoints.")
    parser.add_argument("--filter", default="*.pth.tar", help="Checkpoint glob below input directory.")
    parser.add_argument("--output", required=True, help="Output path; existing files are refused.")
    parser.add_argument("-n", type=int, default=10, help="Top-N checkpoints for the native avg_checkpoints.py command.")
    parser.add_argument("--no-use-ema", action="store_true", help="Do not prefer EMA weights.")
    parser.add_argument("--no-sort", action="store_true", help="Do not sort native averaging candidates by metric.")
    parser.add_argument("--safetensors", action="store_true", help="Use safetensors output.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Safely inspect checkpoint structure as JSON.")
    inspect_parser.add_argument("--checkpoint", required=True, help="Checkpoint path to inspect.")
    inspect_parser.add_argument("--unsafe-load", action="store_true", help="Allow unsafe pickle loading for trusted files only.")
    inspect_parser.add_argument("--sha256", action="store_true", help="Compute full SHA256 of the file.")
    inspect_parser.add_argument("--max-keys", type=int, default=20, help="Maximum keys to include per section.")
    inspect_parser.set_defaults(func=inspect_checkpoint)

    clean_command = subparsers.add_parser("clean-command", help="Print a safe clean_checkpoint.py command.")
    add_common_command_args(clean_command, "clean_checkpoint.py")
    add_clean_args(clean_command)
    clean_command.set_defaults(func=print_clean_command)

    average_command = subparsers.add_parser("average-command", help="Print a safe avg_checkpoints.py command.")
    add_common_command_args(average_command, "avg_checkpoints.py")
    add_average_args(average_command)
    average_command.set_defaults(func=print_average_command)

    average = subparsers.add_parser("average", help="Average matched checkpoints without metric sorting.")
    add_average_args(average)
    average.add_argument("--limit", type=int, default=None, help="Optional first-N limit for this helper implementation.")
    average.set_defaults(func=average_checkpoints)
    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
