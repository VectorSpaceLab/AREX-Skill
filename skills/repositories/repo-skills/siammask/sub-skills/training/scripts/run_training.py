#!/usr/bin/env python3
"""Safe command builder/launcher for SiamMask training workflows.

By default this helper only prints the command and inspects the selected JSON
config. Add --run when you intentionally want to start a training job. Training
is expensive and the legacy scripts call CUDA APIs unconditionally.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

MODES = {
    "base": {
        "experiment": "siammask_base",
        "script": "tools/train_siammask.py",
        "batch": 64,
        "workers": 20,
        "epochs": 20,
        "description": "SiamMask base model with RPN + mask heads",
    },
    "refine": {
        "experiment": "siammask_sharp",
        "script": "tools/train_siammask_refine.py",
        "batch": 64,
        "workers": 20,
        "epochs": 20,
        "description": "SiamMask refine/sharp mask model initialized from a base checkpoint",
    },
    "siamrpn": {
        "experiment": "siamrpn_resnet",
        "script": "tools/train_siamrpn.py",
        "batch": 256,
        "workers": 20,
        "epochs": 20,
        "description": "Unofficial SiamRPN++/ResNet box-tracking baseline",
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compose or run SiamMask training commands.")
    p.add_argument("--repo-root", default=".", help="Path to a SiamMask checkout. Defaults to current directory.")
    p.add_argument("--python", default=sys.executable, help="Python executable to use for training.")
    p.add_argument("--run", action="store_true", help="Execute the command. Omit for dry-run command printing.")
    p.add_argument("--gpu", default=None, help="Optional CUDA_VISIBLE_DEVICES value, e.g. 0 or 0,1,2,3.")
    p.add_argument("--strict", action="store_true", help="Fail when config, pretrained, or resume paths are missing.")
    sub = p.add_subparsers(dest="mode", required=True)
    for name, meta in MODES.items():
        sp = sub.add_parser(name, help=meta["description"])
        sp.add_argument("--config", default="config.json", help="Config JSON path relative to the experiment directory or absolute.")
        sp.add_argument("--batch", type=int, default=meta["batch"])
        sp.add_argument("--workers", type=int, default=meta["workers"])
        sp.add_argument("--epochs", type=int, default=meta["epochs"])
        sp.add_argument("--start-epoch", type=int, default=0)
        sp.add_argument("--lr", type=float, default=None)
        sp.add_argument("--resume", default="")
        sp.add_argument("--pretrained", default="")
        sp.add_argument("--save-dir", default="snapshot")
        sp.add_argument("--log", default="logs/log.txt")
        sp.add_argument("--log-dir", default="board")
    return p.parse_args()


def repo_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    if not (root / "tools" / "train_siammask.py").exists():
        raise SystemExit(f"repo root does not look like SiamMask: {root}")
    return root


def as_path(base: Path, raw: str) -> Path:
    p = Path(raw).expanduser()
    return p if p.is_absolute() else base / p


def warn_or_fail(label: str, path: Path, strict: bool) -> None:
    if path.exists():
        return
    msg = f"warning: {label} not found: {path}"
    if strict:
        raise SystemExit(msg)
    print(msg, file=sys.stderr)


def summarize_config(config_path: Path, experiment_dir: Path) -> None:
    if not config_path.exists():
        return
    try:
        cfg: dict[str, Any] = json.loads(config_path.read_text())
    except Exception as exc:
        print(f"warning: could not parse config {config_path}: {exc}", file=sys.stderr)
        return
    print("config summary:")
    print("  network.arch:", cfg.get("network", {}).get("arch"))
    print("  anchors:", cfg.get("anchors", {}))
    for split in ["train_datasets", "val_datasets"]:
        datasets = cfg.get(split, {}).get("datasets", {})
        if not datasets:
            continue
        print(f"  {split}:")
        for name, spec in datasets.items():
            root = spec.get("root")
            anno = spec.get("anno")
            root_path = as_path(experiment_dir, root) if root else None
            anno_path = as_path(experiment_dir, anno) if anno else None
            print(f"    - {name}: root={root} ({'ok' if root_path and root_path.exists() else 'missing'}), anno={anno} ({'ok' if anno_path and anno_path.exists() else 'missing'})")


def command(args: argparse.Namespace, root: Path) -> tuple[list[str], Path, dict[str, str]]:
    meta = MODES[args.mode]
    cwd = root / "experiments" / meta["experiment"]
    if not cwd.exists():
        raise SystemExit(f"missing experiment directory: {cwd}")
    cfg = as_path(cwd, args.config)
    warn_or_fail("config", cfg, args.strict)
    if args.mode == "refine" and not args.pretrained:
        print("warning: refine training usually needs --pretrained <best base checkpoint>", file=sys.stderr)
    if args.resume:
        warn_or_fail("resume checkpoint", as_path(cwd, args.resume), args.strict)
    if args.pretrained:
        warn_or_fail("pretrained checkpoint", as_path(cwd, args.pretrained), args.strict)
    summarize_config(cfg, cwd)

    cmd = [
        args.python,
        str(root / meta["script"]),
        "--config", args.config,
        "-b", str(args.batch),
        "-j", str(args.workers),
        "--epochs", str(args.epochs),
        "--start-epoch", str(args.start_epoch),
        "--save_dir", args.save_dir,
        "--log", args.log,
        "--log-dir", args.log_dir,
    ]
    if args.lr is not None:
        cmd += ["--lr", str(args.lr)]
    if args.resume:
        cmd += ["--resume", args.resume]
    if args.pretrained:
        cmd += ["--pretrained", args.pretrained]
    env_updates: dict[str, str] = {}
    if args.gpu is not None:
        env_updates["CUDA_VISIBLE_DEVICES"] = args.gpu
    return cmd, cwd, env_updates


def run_or_print(cmd: list[str], cwd: Path, root: Path, run: bool, env_updates: dict[str, str]) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + os.pathsep + str(cwd) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env.update(env_updates)
    print("cwd:", cwd)
    print("cmd:", shlex.join(cmd))
    if env_updates:
        print("env:", " ".join(f"{k}={v}" for k, v in env_updates.items()))
    print("PYTHONPATH prepends:", os.pathsep.join([str(root), str(cwd)]))
    print("warning: native training calls CUDA APIs and can run for hours; keep dry-run unless authorized")
    if not run:
        print("dry-run: add --run before the mode name to execute")
        return 0
    return subprocess.call(cmd, cwd=str(cwd), env=env)


def main() -> int:
    args = parse_args()
    root = repo_root(args.repo_root)
    cmd, cwd, env_updates = command(args, root)
    return run_or_print(cmd, cwd, root, args.run, env_updates)


if __name__ == "__main__":
    raise SystemExit(main())
