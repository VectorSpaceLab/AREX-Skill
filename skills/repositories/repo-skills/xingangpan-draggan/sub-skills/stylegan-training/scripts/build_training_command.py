#!/usr/bin/env python3
"""Print StyleGAN-Human SG2/SG3 training commands without launching training.

The DragGAN checkout carries modified StyleGAN-Human training entry points, but
those files may be used as patches for a complete StyleGAN2-ADA/StyleGAN3
training tree. This helper therefore prints a command and emits support-root
warnings instead of executing training.
"""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def q(cmd):
    return " ".join(shlex.quote(str(x)) for x in cmd)


def shell_command(cwd: Path, cmd: list[object]) -> str:
    return f"cd {shlex.quote(str(cwd))} && {q(cmd)}"


def resolve_under(base: Path, path: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else base / path


def support_warnings(root: Path) -> list[str]:
    checks = [
        root / "train.py",
        root / "training" / "training_loop.py",
        root / "metrics" / "metric_main.py",
        root / "torch_utils" / "training_stats.py",
        root / "dnnlib",
    ]
    return [f"support file/directory not found: {p}" for p in checks if not p.exists()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build safe StyleGAN-Human training commands.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Local DragGAN checkout used to resolve relative data/output paths and bundled patch scripts.")
    parser.add_argument("--version", choices=["sg2", "sg3"], required=True, help="Training script family.")
    parser.add_argument("--training-root", type=Path, help="Complete execution root containing train.py, dnnlib/, training/, metrics/, and torch_utils/. Defaults to the bundled patch-script directory, which may be incomplete for execution.")
    parser.add_argument("--data", required=True, type=Path, help="Dataset directory or zip path; relative paths are resolved under --repo-root in the printed command.")
    parser.add_argument("--outdir", required=True, type=Path, help="Training result directory; relative paths are resolved under --repo-root in the printed command.")
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--batch", type=int, help="Total batch size; required by sg3 and optional for sg2.")
    parser.add_argument("--gamma", type=float, help="R1 gamma; required by common sg3 recipes.")
    parser.add_argument("--cfg", default=None, help="Config name, e.g. shhq for sg2 or stylegan3-r for sg3.")
    parser.add_argument("--mirror", choices=["0", "1", "True", "False"], default="1")
    parser.add_argument("--aug", default="noaug")
    parser.add_argument("--square", choices=["True", "False", "0", "1"], default="False")
    parser.add_argument("--snap", type=int, default=250)
    parser.add_argument("--kimg", type=int, help="Optional short debug duration or full run kimg.")
    parser.add_argument("--resume", help="Optional network pickle or URL to resume from.")
    parser.add_argument("--metrics", help="Optional metrics list, e.g. none or fid50k_full.")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--dry-run-flag", action="store_true", help="Include -n/--dry-run in the printed command when supported.")
    parser.add_argument("--validate-data-path", action="store_true", help="Fail if the resolved --data path does not exist on this machine.")
    args = parser.parse_args()

    repo = args.repo_root.expanduser().resolve()
    patch_root = repo / "stylegan_human" / "training_scripts" / args.version
    training_root = args.training_root.expanduser().resolve() if args.training_root else patch_root
    data = resolve_under(repo, args.data)
    outdir = resolve_under(repo, args.outdir)
    if args.validate_data_path and not data.exists():
        print(f"ERROR: dataset path does not exist: {data}", file=sys.stderr)
        return 2

    warnings = support_warnings(training_root)
    if args.training_root is None and warnings:
        warnings.insert(0, "default training root appears to contain StyleGAN-Human patch files rather than a complete training tree; apply/copy the modified train/network files into a full StyleGAN2-ADA or StyleGAN3 root, or pass --training-root to that prepared root before executing.")

    cmd: list[object]
    if args.version == "sg2":
        cmd = ["python", "train.py", "--outdir", outdir, "--data", data, "--gpus", args.gpus, "--aug", args.aug, "--mirror", args.mirror, "--snap", args.snap, "--square", args.square]
        cmd += ["--cfg", args.cfg or "shhq"]
        if args.batch: cmd += ["--batch", args.batch]
        if args.gamma is not None: cmd += ["--gamma", args.gamma]
    else:
        cmd = ["python", "train.py", "--outdir", outdir, "--data", data, "--gpus", args.gpus, "--batch", args.batch or 32, "--gamma", args.gamma if args.gamma is not None else 12.4, "--cfg", args.cfg or "stylegan3-r", "--mirror", args.mirror, "--aug", args.aug, "--square", args.square, "--snap", args.snap]
    if args.kimg: cmd += ["--kimg", args.kimg]
    if args.resume:
        resume = args.resume
        if not (resume.startswith("http://") or resume.startswith("https://")):
            resume = str(resolve_under(repo, Path(resume)))
        cmd += ["--resume", resume]
    if args.metrics: cmd += ["--metrics", args.metrics]
    if args.seed is not None: cmd += ["--seed", args.seed]
    if args.workers is not None: cmd += ["--workers", args.workers]
    if args.dry_run_flag: cmd += ["--dry-run"]

    for warning in warnings:
        print(f"WARNING: {warning}")
    print(shell_command(training_root, cmd))
    if args.gpus < 8:
        print("NOTE: README paper-scale examples use 8 GPUs; this command is a smaller/debug-style adaptation.")
    print("This helper only prints a command. Review data access, GPU memory, support modules, and output storage before running it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
