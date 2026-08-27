#!/usr/bin/env python3
"""Parse a JSONC SR config and print an infer.py command without running it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable


def strip_jsonc_comments(text: str) -> str:
    """Remove // comments while preserving // inside JSON strings."""
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_jsonc(path: Path) -> dict[str, Any]:
    try:
        return json.loads(strip_jsonc_comments(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        raise SystemExit(f"Config not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse JSON-with-comments config {path}: {exc}") from exc


def nested_get(data: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def resolve_run_path(repo_root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return repo_root / path


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def checkpoint_errors(
    *,
    repo_root: Path,
    resume_state: str | None,
    require: bool,
    skip_files: bool,
) -> list[str]:
    errors: list[str] = []
    if not resume_state:
        if require:
            errors.append("path.resume_state is empty; edit the config to a checkpoint stem before pretrained inference.")
        return errors

    if resume_state.endswith("_gen.pth") or resume_state.endswith("_opt.pth"):
        errors.append(
            "path.resume_state must be the checkpoint stem, not a suffixed file; "
            "the repo appends _gen.pth internally."
        )
        return errors

    if not skip_files:
        gen_path = resolve_run_path(repo_root, resume_state + "_gen.pth")
        if gen_path is not None and not gen_path.exists():
            errors.append(f"Missing generator checkpoint expected by infer.py: {gen_path}")
    return errors


def expected_img_dirs(dataset: dict[str, Any]) -> list[str]:
    low = dataset.get("l_resolution")
    high = dataset.get("r_resolution")
    mode = dataset.get("mode")
    dirs = [f"sr_{low}_{high}", f"hr_{high}"]
    if mode == "LRHR":
        dirs.insert(0, f"lr_{low}")
    return dirs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a safe infer.py command after parsing the repo's comment-bearing config."
    )
    parser.add_argument("-c", "--config", default="config/sr_sr3_64_512.json", help="SR inference config path")
    parser.add_argument("--repo-root", default=".", help="Checkout root used to resolve relative config/data/checkpoint paths")
    parser.add_argument("--python", default="python", help="Python executable to place in the printed command")
    parser.add_argument("--gpu-ids", help="Comma-separated GPU ids for infer.py -gpu")
    parser.add_argument("--debug", action="store_true", help="Add infer.py -debug")
    parser.add_argument("--enable-wandb", action="store_true", help="Add infer.py -enable_wandb")
    parser.add_argument("--log-infer", action="store_true", help="Add infer.py -log_infer")
    parser.add_argument("--require-resume-state", action="store_true", help="Require path.resume_state and its _gen.pth file")
    parser.add_argument("--skip-checkpoint-files", action="store_true", help="Do not check that checkpoint files exist")
    parser.add_argument("--check-data", action="store_true", help="Check expected image-layout directories when datatype is img")
    parser.add_argument("--strict", action="store_true", help="Fail on workflow/config mismatches instead of printing warnings")
    parser.add_argument("--command-only", action="store_true", help="Print only the shell command")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    config_arg = Path(args.config).expanduser()
    config_path = config_arg if config_arg.is_absolute() else repo_root / config_arg
    opt = load_jsonc(config_path)

    warnings: list[str] = []
    errors: list[str] = []

    if nested_get(opt, ["model", "diffusion", "conditional"]) is not True:
        msg = "Config model.diffusion.conditional is not true; infer.py super-resolution normally needs a conditional SR config."
        (errors if args.strict else warnings).append(msg)
    if nested_get(opt, ["model", "unet", "in_channel"]) != 6:
        warnings.append("Expected model.unet.in_channel to be 6 for stock conditional RGB SR inference.")
    if "val" not in opt.get("datasets", {}):
        errors.append("Config has no datasets.val section for infer.py validation data.")

    resume_state = nested_get(opt, ["path", "resume_state"])
    errors.extend(
        checkpoint_errors(
            repo_root=repo_root,
            resume_state=resume_state,
            require=args.require_resume_state,
            skip_files=args.skip_checkpoint_files,
        )
    )

    val_dataset = nested_get(opt, ["datasets", "val"], {}) or {}
    if args.check_data and val_dataset:
        datatype = val_dataset.get("datatype")
        dataroot = resolve_run_path(repo_root, val_dataset.get("dataroot"))
        if datatype == "img":
            for dirname in expected_img_dirs(val_dataset):
                candidate = dataroot / dirname if dataroot is not None else None
                if candidate is None or not candidate.is_dir():
                    errors.append(f"Missing expected validation image directory: {candidate}")
        elif datatype == "lmdb":
            if dataroot is None or not dataroot.exists():
                errors.append(f"LMDB dataroot does not exist: {dataroot}")
        else:
            warnings.append(f"Unrecognized datasets.val.datatype: {datatype!r}")

    if errors:
        for item in warnings:
            print(f"WARNING: {item}", file=sys.stderr)
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 2

    command = [args.python, "infer.py", "-c", str(config_arg), "-p", "val"]
    if args.gpu_ids:
        command.extend(["-gpu", args.gpu_ids])
    if args.debug:
        command.append("-debug")
    if args.enable_wandb:
        command.append("-enable_wandb")
    if args.log_infer:
        command.append("-log_infer")

    if args.command_only:
        print(shell_join(command))
        return 0

    print("# infer.py command preflight")
    print(f"# config: {config_arg}")
    print(f"# model: {nested_get(opt, ['model', 'which_model_G'])}; conditional={nested_get(opt, ['model', 'diffusion', 'conditional'])}; image_size={nested_get(opt, ['model', 'diffusion', 'image_size'])}")
    print(f"# val data: datatype={val_dataset.get('datatype')}; mode={val_dataset.get('mode')}; dataroot={val_dataset.get('dataroot')}; data_len={val_dataset.get('data_len')}")
    print(f"# resume_state: {resume_state!r}")
    for item in warnings:
        print(f"# WARNING: {item}")
    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
