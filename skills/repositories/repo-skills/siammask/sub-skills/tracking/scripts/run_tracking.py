#!/usr/bin/env python3
"""Safe command builder/launcher for SiamMask tracking and evaluation workflows.

Default behavior is dry-run: the helper validates paths, prints the exact native
command it will launch inside the selected checkout, and exits. Add --run when
you intentionally want to execute the command. The helper sets PYTHONPATH so the
legacy repo scripts can import utils/, models/, datasets/, and experiment-local
custom.py modules.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

EXPERIMENTS = ["siammask_sharp", "siammask_base", "siamrpn_resnet"]


def root_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compose or run SiamMask demo, benchmark, eval, and tuning commands.")
    p.add_argument("--repo-root", default=".", help="Path to a SiamMask checkout. Defaults to the current directory.")
    p.add_argument("--python", default=sys.executable, help="Python executable to use for the checkout command.")
    p.add_argument("--run", action="store_true", help="Execute the command. Omit for safe dry-run command printing.")
    p.add_argument("--strict", action="store_true", help="Fail if checkpoint/config/result paths that can be checked are missing.")
    sub = p.add_subparsers(dest="mode", required=True)

    demo = sub.add_parser("demo", help="Run the interactive single-sequence demo.")
    demo.add_argument("--experiment", choices=EXPERIMENTS, default="siammask_sharp")
    demo.add_argument("--resume", required=True, help="Checkpoint path, relative to the experiment cwd or absolute.")
    demo.add_argument("--config", default="config_davis.json", help="Config JSON path, relative to the experiment cwd or absolute.")
    demo.add_argument("--base-path", default="data/tennis", help="Image-sequence directory. Relative paths are resolved under repo root.")
    demo.add_argument("--cpu", action="store_true", help="Pass the native --cpu flag; note that the legacy demo still auto-selects visible CUDA.")

    test = sub.add_parser("test", help="Run benchmark tracking on VOT/DAVIS/YouTube-VOS style data.")
    test.add_argument("--experiment", choices=EXPERIMENTS, default="siammask_sharp")
    test.add_argument("--resume", required=True)
    test.add_argument("--config", default="config_vot18.json")
    test.add_argument("--dataset", default="VOT2018")
    test.add_argument("--mask", action="store_true")
    test.add_argument("--refine", action="store_true")
    test.add_argument("--cpu", action="store_true")
    test.add_argument("--visualization", action="store_true")
    test.add_argument("--save-mask", action="store_true", dest="save_mask")
    test.add_argument("--gt", action="store_true")
    test.add_argument("--video", default="")
    test.add_argument("--log", default="log_test.txt")

    ev = sub.add_parser("eval", help="Evaluate VOT result directories with the bundled VOT evaluator.")
    ev.add_argument("--dataset", required=True)
    ev.add_argument("--result-dir", required=True)
    ev.add_argument("--tracker-prefix", required=True)
    ev.add_argument("--num", type=int, default=1)
    ev.add_argument("--show-video-level", action="store_true")

    tv = sub.add_parser("tune-vot", help="Run VOT hyperparameter tuning.")
    add_tune_args(tv, default_config="config_vot18.json")

    ts = sub.add_parser("tune-vos", help="Run DAVIS/YouTube-VOS hyperparameter tuning; CUDA is required by the legacy script.")
    add_tune_args(ts, default_config="config_davis.json")
    return p


def add_tune_args(p: argparse.ArgumentParser, default_config: str) -> None:
    p.add_argument("--experiment", choices=EXPERIMENTS, default="siammask_sharp")
    p.add_argument("--resume", required=True)
    p.add_argument("--config", default=default_config)
    p.add_argument("--dataset", default="VOT2018")
    p.add_argument("--mask", action="store_true")
    p.add_argument("--refine", action="store_true")
    p.add_argument("--visualization", action="store_true")
    p.add_argument("--penalty-k", default=None, help="Range string such as 0.08,0.13,0.01.")
    p.add_argument("--lr", default=None, help="Range string such as 0.3,0.35,0.01.")
    p.add_argument("--window-influence", default=None, help="Range string such as 0.38,0.44,0.01.")
    p.add_argument("--search-region", default=None, help="Range string such as 255,256,16.")
    p.add_argument("--log", default=None)


def resolve_repo(path: str) -> Path:
    root = Path(path).expanduser().resolve()
    if not (root / "tools" / "test.py").exists():
        raise SystemExit(f"repo root does not look like SiamMask: {root}")
    return root


def exp_cwd(root: Path, name: str) -> Path:
    cwd = root / "experiments" / name
    if not cwd.exists():
        raise SystemExit(f"missing experiment directory: {cwd}")
    return cwd


def maybe_path(base: Path, raw: str) -> Path:
    p = Path(raw).expanduser()
    return p if p.is_absolute() else base / p


def warn_or_fail(label: str, path: Path, strict: bool) -> None:
    if path.exists():
        return
    msg = f"warning: {label} not found: {path}"
    if strict:
        raise SystemExit(msg)
    print(msg, file=sys.stderr)


def append_flag(cmd: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        cmd.append(flag)


def command_for(args: argparse.Namespace, root: Path) -> tuple[list[str], Path, list[str]]:
    warnings: list[str] = []
    if args.mode == "demo":
        cwd = exp_cwd(root, args.experiment)
        warn_or_fail("config", maybe_path(cwd, args.config), args.strict)
        warn_or_fail("checkpoint", maybe_path(cwd, args.resume), args.strict)
        base = maybe_path(root, args.base_path)
        warn_or_fail("base image sequence", base, args.strict)
        cmd = [args.python, str(root / "tools" / "demo.py"), "--resume", args.resume, "--config", args.config, "--base_path", str(base)]
        append_flag(cmd, "--cpu", args.cpu)
        warnings.append("demo uses OpenCV GUI ROI selection; use a desktop/display session. The legacy --cpu flag is parsed but CUDA is still auto-selected when visible.")
        return cmd, cwd, warnings

    if args.mode == "test":
        cwd = exp_cwd(root, args.experiment)
        warn_or_fail("config", maybe_path(cwd, args.config), args.strict)
        warn_or_fail("checkpoint", maybe_path(cwd, args.resume), args.strict)
        cmd = [args.python, str(root / "tools" / "test.py"), "--config", args.config, "--resume", args.resume, "--dataset", args.dataset, "--log", args.log]
        append_flag(cmd, "--mask", args.mask)
        append_flag(cmd, "--refine", args.refine)
        append_flag(cmd, "--cpu", args.cpu)
        append_flag(cmd, "--visualization", args.visualization)
        append_flag(cmd, "--save_mask", args.save_mask)
        append_flag(cmd, "--gt", args.gt)
        if args.video:
            cmd += ["--video", args.video]
        return cmd, cwd, warnings

    if args.mode == "eval":
        warn_or_fail("result directory", maybe_path(root, args.result_dir), args.strict)
        cmd = [args.python, str(root / "tools" / "eval.py"), "--dataset", args.dataset, "--result_dir", args.result_dir, "--tracker_prefix", args.tracker_prefix, "--num", str(args.num)]
        append_flag(cmd, "--show_video_level", args.show_video_level)
        return cmd, root, warnings

    if args.mode in {"tune-vot", "tune-vos"}:
        cwd = exp_cwd(root, args.experiment)
        script = "tune_vot.py" if args.mode == "tune-vot" else "tune_vos.py"
        warn_or_fail("config", maybe_path(cwd, args.config), args.strict)
        warn_or_fail("checkpoint", maybe_path(cwd, args.resume), args.strict)
        cmd = [args.python, str(root / "tools" / script), "--config", args.config, "--dataset", args.dataset, "--resume", args.resume]
        append_flag(cmd, "--mask", args.mask)
        append_flag(cmd, "--refine", args.refine)
        append_flag(cmd, "--visualization", args.visualization)
        for flag, value in [("--penalty-k", args.penalty_k), ("--lr", args.lr), ("--window-influence", args.window_influence), ("--search-region", args.search_region), ("--log", args.log)]:
            if value:
                cmd += [flag, value]
        if args.mode == "tune-vos":
            warnings.append("tune-vos calls model.cuda() unconditionally; run only in a CUDA-capable environment.")
        return cmd, cwd, warnings

    raise AssertionError(args.mode)


def run_or_print(cmd: list[str], cwd: Path, repo_root: Path, run: bool) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + str(cwd) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    print("cwd:", cwd)
    print("cmd:", shlex.join(cmd))
    print("PYTHONPATH prepends:", os.pathsep.join([str(repo_root), str(cwd)]))
    if not run:
        print("dry-run: add --run before the mode name to execute")
        return 0
    return subprocess.call(cmd, cwd=str(cwd), env=env)


def main() -> int:
    p = root_parser()
    args = p.parse_args()
    root = resolve_repo(args.repo_root)
    cmd, cwd, warnings = command_for(args, root)
    for warning in warnings:
        print("warning:", warning, file=sys.stderr)
    return run_or_print(cmd, cwd, root, args.run)


if __name__ == "__main__":
    raise SystemExit(main())
