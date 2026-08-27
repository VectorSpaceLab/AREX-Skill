#!/usr/bin/env python3
"""Preflight and optionally run the source style-transfer trainer.

The default is dry-run. Training is expensive and writes checkpoints, norms,
logs, and probe artifacts; this helper never downloads or deletes anything.
"""
from __future__ import print_function

import argparse
import ast
import os
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile


def make_parser():
    parser = argparse.ArgumentParser(description="Preflight style-transfer training/resume; dry-run by default.")
    parser.add_argument("--source-root", required=True, help="User checkout containing style_transfer/")
    parser.add_argument("--data-path", required=True, help="NPZ selected by the source config")
    parser.add_argument("--normalization-dir", required=True, help="Config extra_data_dir")
    parser.add_argument("--checkpoint-dir", required=True, help="Expected source-derived <name>/pth directory")
    parser.add_argument("--name", required=True, help="Experiment name controlling source output paths")
    parser.add_argument("--batch-size", type=int, default=128, help="Source --batch_size (default 128; avoids source name/batch-size typo)")
    parser.add_argument("--config", default="config", help="Config module (default: config)")
    parser.add_argument("--python-executable", default=sys.executable, help="Python used by --execute")
    parser.add_argument("--allow-resume", action="store_true", help="Acknowledge source auto-resume from complete checkpoints")
    parser.add_argument("--execute", action="store_true", help="Start the long-running source trainer")
    return parser


def config_literals(path):
    """Read simple literal Config assignments without importing user code."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return {}
    values = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Config":
            for statement in node.body:
                if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                    try:
                        values[statement.targets[0].id] = ast.literal_eval(statement.value)
                    except (ValueError, TypeError):
                        pass
            break
    return values


def npz_members_issue(path):
    try:
        with zipfile.ZipFile(str(path)) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile) as exc:
        return "NPZ is unreadable: %s (%s)" % (path, exc)
    missing = sorted(set(("train.npy", "test.npy", "trainfull.npy")) - names)
    if missing:
        return "NPZ is missing source subset member(s): %s" % ", ".join(missing)
    return None


def stats_issue(path):
    try:
        with zipfile.ZipFile(str(path)) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile) as exc:
        return "normalization archive is unreadable: %s (%s)" % (path, exc)
    missing = sorted(set(("mean.npy", "std.npy")) - names)
    if missing:
        return "normalization archive %s is missing key(s): %s" % (path, ", ".join(name[:-4] for name in missing))
    return None


def checkpoint_files(directory, token):
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file() and token in path.name and path.suffix == ".pt")


def preflight(args):
    errors = []
    warnings = []
    root = Path(args.source_root).expanduser()
    data = Path(args.data_path).expanduser()
    norms = Path(args.normalization_dir).expanduser()
    checkpoint = Path(args.checkpoint_dir).expanduser()
    entry = root / "style_transfer" / "train.py"
    config_file = root / "style_transfer" / (args.config + ".py")
    if not root.is_dir():
        errors.append("source root is not a directory: %s" % root)
    if not entry.is_file():
        errors.append("missing source training entry point: %s" % entry)
    if not config_file.is_file():
        errors.append("missing source config file: %s" % config_file)
        literals = {}
    else:
        literals = config_literals(config_file)

    if not data.is_file() or data.suffix != ".npz":
        errors.append("data-path must be an existing .npz file: %s" % data)
    else:
        issue = npz_members_issue(data)
        if issue:
            errors.append(issue)
        warnings.append("NPZ members checked without loading object arrays or validating 132-channel motion")

    data_filename = literals.get("data_filename")
    if isinstance(data_filename, str):
        expected_data = root / "style_transfer" / "data" / data_filename
        expected_norms = root / "style_transfer" / "data" / (Path(data_filename).stem + "_norms")
        if data != expected_data:
            errors.append("source config derives data-path %s, not %s" % (expected_data, data))
        if norms != expected_norms:
            errors.append("source config derives normalization-dir %s, not %s" % (expected_norms, norms))
    else:
        warnings.append("could not statically derive data_filename from custom config; verify data/norm paths")

    if norms.exists() and not norms.is_dir():
        errors.append("normalization path is not a directory: %s" % norms)
    elif not norms.exists() and not norms.parent.is_dir():
        errors.append("normalization parent does not exist: %s" % norms.parent)
    elif norms.parent.exists() and not os.access(str(norms.parent), os.W_OK):
        errors.append("normalization parent is not writable: %s" % norms.parent)
    norm_names = ("train_content.npz", "train_style3d.npz", "train_style2d.npz")
    present = [name for name in norm_names if (norms / name).is_file()]
    if present and len(present) != len(norm_names):
        errors.append("normalization set is partial; missing: %s" % ", ".join(sorted(set(norm_names) - set(present))))
    elif not present:
        warnings.append("fresh training will compute train content/style3d/style2d norms")
    else:
        for name in norm_names:
            issue = stats_issue(norms / name)
            if issue:
                errors.append(issue)
        warnings.append("existing norms will be reused; verify dataset/config provenance")

    expected_checkpoint = root / "style_transfer" / args.name / "pth"
    if checkpoint != expected_checkpoint:
        errors.append("source config derives checkpoint-dir %s, not %s" % (expected_checkpoint, checkpoint))
    if checkpoint.exists() and not checkpoint.is_dir():
        errors.append("checkpoint path is not a directory: %s" % checkpoint)
    gen = checkpoint_files(checkpoint, "gen")
    dis = checkpoint_files(checkpoint, "dis")
    opt = checkpoint / "optimizer.pt"
    complete = bool(gen and dis and opt.is_file())
    partial = bool(gen or dis or opt.exists()) and not complete
    if partial:
        errors.append("checkpoint set is partial; source resume requires gen*.pt, dis*.pt, and optimizer.pt")
    elif complete and not args.allow_resume:
        errors.append("complete checkpoint set exists; pass --allow-resume to acknowledge auto-resume")
    elif complete:
        warnings.append("source resumes lexicographically latest gen/dis and optimizer/schedulers")
    else:
        warnings.append("no complete checkpoint; source starts from iteration zero")

    if not args.name or Path(args.name).name != args.name or args.name in (".", ".."):
        errors.append("name must be one non-empty path component")
    if args.batch_size is not None and args.batch_size < 1:
        errors.append("batch-size must be positive")
    if literals.get("num_classes") is not None:
        warnings.append("config num_classes=%s; verify it matches Xia/BFA labels" % literals["num_classes"])
    if literals.get("max_iter") is not None:
        warnings.append("config max_iter=%s; --execute starts a long run" % literals["max_iter"])
    warnings.append("unmodified train.py imports TensorBoardX and plotting dependencies at startup")
    warnings.append("dry-run performs no imports, directory creation, normalization, resume, or writes")
    return errors, warnings


def build_command(args):
    return [
        args.python_executable, "style_transfer/train.py", "--name", args.name,
        "--batch_size", str(args.batch_size), "--config", args.config,
    ]


def main(argv=None):
    args = make_parser().parse_args(argv)
    errors, warnings = preflight(args)
    for warning in warnings:
        print("warning: %s" % warning, file=sys.stderr)
    if errors:
        for error in errors:
            print("error: %s" % error, file=sys.stderr)
        return 2
    print("training preflight: ok")
    print("working directory: <user-supplied source root>")
    print("command: %s" % shlex.join(build_command(args)))
    if not args.execute:
        print("dry-run only; pass --execute to start expensive training")
        return 0
    return subprocess.call(build_command(args), cwd=str(Path(args.source_root).expanduser()))


if __name__ == "__main__":
    raise SystemExit(main())
