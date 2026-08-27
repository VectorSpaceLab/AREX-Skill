#!/usr/bin/env python3
"""Preflight and optionally run one source style-transfer inference.

The generated helper does not import the project.  A user supplies the source
checkout and all data/checkpoint paths explicitly.  Dry-run is the default.
"""
from __future__ import print_function

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile
import re


def make_parser():
    parser = argparse.ArgumentParser(
        description="Preflight 3D-BVH or OpenPose-JSON style transfer; dry-run by default."
    )
    parser.add_argument("--source-root", required=True, help="User checkout containing style_transfer/")
    parser.add_argument("--content-src", required=True, help="Existing content BVH")
    parser.add_argument("--style-src", required=True, help="Existing lowercase .bvh or OpenPose JSON directory")
    parser.add_argument("--output-dir", required=True, help="Output directory for raw.bvh and fixed.bvh")
    parser.add_argument("--checkpoint-dir", required=True, help="Expected source-derived <name>/pth directory")
    parser.add_argument("--normalization-dir", required=True, help="Directory containing train_* norm archives")
    parser.add_argument("--name", default="pretrained", help="Source experiment name (default: pretrained)")
    parser.add_argument("--batch-size", type=int, default=None, help="Optional source --batch_size")
    parser.add_argument("--config", default="config", help="Source config module (default: config)")
    parser.add_argument("--python-executable", default=sys.executable, help="Python used by --execute")
    parser.add_argument("--allow-overwrite-output", action="store_true", help="Allow existing raw/fixed files")
    parser.add_argument("--execute", action="store_true", help="Invoke the source after preflight")
    return parser


def checkpoint_files(directory, token):
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and token in path.name and path.suffix == ".pt"
    )


def stats_issue(path):
    if not path.is_file():
        return "missing normalization archive: %s" % path
    try:
        with zipfile.ZipFile(str(path)) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile) as exc:
        return "normalization archive is unreadable: %s: %s" % (path, exc)
    missing = sorted(set(("mean.npy", "std.npy")) - names)
    if missing:
        return "normalization archive %s is missing key(s): %s" % (
            path, ", ".join(name[:-4] for name in missing)
        )
    return None


def preflight(args):
    errors = []
    warnings = []
    root = Path(args.source_root).expanduser()
    content = Path(args.content_src).expanduser()
    style = Path(args.style_src).expanduser()
    output = Path(args.output_dir).expanduser()
    checkpoint = Path(args.checkpoint_dir).expanduser()
    norms = Path(args.normalization_dir).expanduser()

    entry = root / "style_transfer" / "test.py"
    config_file = root / "style_transfer" / (args.config + ".py")
    if not root.is_dir():
        errors.append("source root is not a directory: %s" % root)
    if not entry.is_file():
        errors.append("missing source entry point: %s" % entry)
    if not config_file.is_file():
        errors.append("missing source config file: %s" % config_file)
    if not content.is_file() or content.suffix != ".bvh":
        errors.append("content must be an existing lowercase-.bvh file: %s" % content)

    if style.name.endswith(".bvh"):
        style_mode = "3d"
        if not style.is_file():
            errors.append("3D style is not an existing lowercase-.bvh file: %s" % style)
    else:
        style_mode = "2d-json"
        if not style.is_dir():
            errors.append("non-.bvh style must be an existing OpenPose JSON directory: %s" % style)

    if output.exists() and output.is_file():
        errors.append("output path is a file: %s" % output)
    elif output.exists() and not args.allow_overwrite_output:
        existing = [name for name in ("raw.bvh", "fixed.bvh") if (output / name).exists()]
        if existing:
            errors.append("output already contains %s; use a new directory or --allow-overwrite-output" % ", ".join(existing))
    elif not output.parent.is_dir():
        errors.append("output parent does not exist: %s" % output.parent)
    elif not os.access(str(output.parent), os.W_OK):
        errors.append("output parent is not writable: %s" % output.parent)

    expected_checkpoint = root / "style_transfer" / args.name / "pth"
    if checkpoint != expected_checkpoint:
        errors.append("source Config.initialize derives checkpoint-dir %s for this name, not %s" % (expected_checkpoint, checkpoint))
    if not checkpoint.is_dir():
        errors.append("checkpoint directory is missing: %s" % checkpoint)
    else:
        if not checkpoint_files(checkpoint, "gen"):
            errors.append("no generator *gen*.pt checkpoint in %s" % checkpoint)
        if not checkpoint_files(checkpoint, "dis"):
            errors.append("no discriminator *dis*.pt checkpoint in %s" % checkpoint)
        if not (checkpoint / "optimizer.pt").is_file():
            errors.append("missing optimizer.pt in %s" % checkpoint)

    if not norms.is_dir():
        errors.append("normalization directory is missing: %s" % norms)
    if args.config == "config":
        expected_norms = root / "style_transfer" / "data" / "xia_norms"
        if norms != expected_norms:
            errors.append("default config derives normalization-dir %s, not %s" % (expected_norms, norms))
    for filename in ("train_content.npz", "train_style3d.npz"):
        issue = stats_issue(norms / filename)
        if issue:
            errors.append(issue)

    if style_mode == "2d-json":
        json_norm = root / "style_transfer" / "data" / "treadmill_norm" / "test2d.npz"
        issue = stats_issue(json_norm)
        if issue:
            errors.append("OpenPose branch uses its source-relative hard-coded 2D norm; %s" % issue)
        warnings.append("normalization-dir does not override the source hard-coded test2d.npz")
    if not args.name or Path(args.name).name != args.name or args.name in (".", ".."):
        errors.append("--name must be one non-empty path component")
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", args.config):
        errors.append("--config must be a simple source module name (letters, digits, underscore)")
    if args.batch_size is not None and args.batch_size < 1:
        errors.append("--batch-size must be positive")
    warnings.append("source style branch selected: %s" % style_mode)
    warnings.append("dry-run performs no imports, output creation, checkpoint copy, or cleanup")
    return errors, warnings


def build_command(args):
    command = [
        args.python_executable,
        "style_transfer/test.py",
        "--name", args.name,
        "--config", args.config,
        "--content_src", str(Path(args.content_src).expanduser()),
        "--style_src", str(Path(args.style_src).expanduser()),
        "--output_dir", str(Path(args.output_dir).expanduser()),
    ]
    if args.batch_size is not None:
        command.extend(["--batch_size", str(args.batch_size)])
    return command


def main(argv=None):
    args = make_parser().parse_args(argv)
    errors, warnings = preflight(args)
    for warning in warnings:
        print("warning: %s" % warning, file=sys.stderr)
    if errors:
        for error in errors:
            print("error: %s" % error, file=sys.stderr)
        return 2
    command = build_command(args)
    print("style-transfer preflight: ok")
    print("working directory: <user-supplied source root>")
    print("command: %s" % shlex.join(command))
    if not args.execute:
        print("dry-run only; pass --execute after reviewing the command")
        return 0
    return subprocess.call(command, cwd=str(Path(args.source_root).expanduser()))


if __name__ == "__main__":
    raise SystemExit(main())
