#!/usr/bin/env python3
"""Preflight and optionally run Xia/BFA BVH-to-NPZ export.

The default is a no-write dry run. This helper does not import the project,
download data, copy bulk data, or delete existing outputs.
"""
from __future__ import print_function

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

REQUIRED_KEYS = {
    "xia": ("style_names", "content_full_names", "content_names", "content_test_cnt"),
    "bfa": ("style_names",),
}


def make_parser():
    parser = argparse.ArgumentParser(description="Preflight Xia/BFA dataset export; dry-run by default.")
    parser.add_argument("--source-root", required=True, help="User checkout containing style_transfer/")
    parser.add_argument("--dataset", choices=("xia", "bfa"), required=True)
    parser.add_argument("--bvh-path", required=True, help="Directory of dataset BVHs")
    parser.add_argument("--output-path", required=True, help="Output prefix; source adds .npz and .info")
    parser.add_argument("--dataset-config", required=True, help="Dataset YAML")
    parser.add_argument("--window", type=int, default=32, help="Window length (source shell uses 32)")
    parser.add_argument("--window-step", type=int, default=8, help="Window step (source shell uses 8)")
    parser.add_argument("--python-executable", default=sys.executable, help="Python used by --execute")
    parser.add_argument("--allow-overwrite", action="store_true", help="Allow existing output prefix artifacts")
    parser.add_argument("--execute", action="store_true", help="Run source exporter after preflight")
    return parser


def yaml_top_keys(text):
    # Dependency-free presence check for the plain top-level mappings used by
    # the checked-in YAML. It intentionally does not pretend to parse YAML.
    return set(re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\s*:", text))


def filename_issue(dataset, name):
    if not name.endswith(".bvh") or name == "rest.bvh":
        return None
    parts = name[:-4].split("_")
    if dataset == "xia":
        if len(parts) != 3:
            return "expected <style>_<content-index>_<suffix>.bvh"
        if not parts[1].isdigit() or int(parts[1]) < 1:
            return "content index must be a positive integer"
    elif len(parts) != 2:
        return "expected <style>_<suffix>.bvh"
    return None


def preflight(args):
    errors = []
    warnings = []
    root = Path(args.source_root).expanduser()
    bvh_path = Path(args.bvh_path).expanduser()
    output = Path(args.output_path).expanduser()
    config = Path(args.dataset_config).expanduser()
    for required in (
        root / "style_transfer" / "data_proc" / "export_train.py",
        root / "style_transfer" / "global_info" / "skeleton_CMU.yml",
        root / "style_transfer" / "global_info" / "rest.bvh",
    ):
        if not required.is_file():
            errors.append("missing source artifact: %s" % required)
    if not root.is_dir():
        errors.append("source root is not a directory: %s" % root)

    if not bvh_path.is_dir():
        errors.append("BVH input directory is missing: %s" % bvh_path)
        bvh_files = []
    else:
        bvh_files = sorted(
            path for path in bvh_path.iterdir()
            if path.is_file() and path.name.endswith(".bvh") and path.name != "rest.bvh"
        )
        if not bvh_files:
            errors.append("no lowercase-.bvh files excluding rest.bvh in %s" % bvh_path)
        bad = [(path.name, filename_issue(args.dataset, path.name)) for path in bvh_files]
        bad = [(name, issue) for name, issue in bad if issue]
        if bad:
            errors.append("invalid dataset filename(s): %s" % "; ".join("%s (%s)" % pair for pair in bad[:5]))

    if not config.is_file():
        errors.append("dataset YAML is missing: %s" % config)
    else:
        try:
            text = config.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append("cannot read dataset YAML %s: %s" % (config, exc))
        else:
            missing = [key for key in REQUIRED_KEYS[args.dataset] if key not in yaml_top_keys(text)]
            if missing:
                errors.append("dataset YAML is missing top-level key(s): %s" % ", ".join(missing))

    if output.suffix in (".npz", ".info"):
        errors.append("output-path is a prefix; omit .npz and .info")
    if not output.parent.is_dir():
        errors.append("output parent directory does not exist: %s" % output.parent)
    elif not os.access(str(output.parent), os.W_OK):
        errors.append("output parent is not writable: %s" % output.parent)
    artifacts = [Path(str(output) + ".npz"), Path(str(output) + ".info")]
    if args.dataset == "xia":
        artifacts.append(Path(str(output) + "_test"))
    existing = [path for path in artifacts if path.exists()]
    if existing and not args.allow_overwrite:
        errors.append("output artifact(s) already exist: %s" % ", ".join(map(str, existing)))
    if args.window < 12:
        errors.append("window must be at least 12 for source padding assumptions")
    if args.window % 4 != 0:
        errors.append("window must be divisible by 4 for source temporal/model assumptions")
    if args.window_step < 1:
        errors.append("window-step must be positive")
    if args.window_step > args.window:
        warnings.append("window-step exceeds window and may leave gaps")
    warnings.append("active Xia/BFA exporter downsamples BVH by 4; no CLI downsample override exists")
    if args.dataset == "xia":
        warnings.append("Xia export copies selected test BVHs into <output>_test")
    warnings.append("dry-run does not parse BVH contents or write NPZ/info/test artifacts")
    return errors, warnings, bvh_files


def build_command(args):
    return [
        args.python_executable,
        "style_transfer/data_proc/export_train.py",
        "--dataset", args.dataset,
        "--bvh_path", str(Path(args.bvh_path).expanduser()),
        "--output_path", str(Path(args.output_path).expanduser()),
        "--window", str(args.window),
        "--window_step", str(args.window_step),
        "--dataset_config", str(Path(args.dataset_config).expanduser()),
    ]


def main(argv=None):
    args = make_parser().parse_args(argv)
    errors, warnings, bvh_files = preflight(args)
    for warning in warnings:
        print("warning: %s" % warning, file=sys.stderr)
    if errors:
        for error in errors:
            print("error: %s" % error, file=sys.stderr)
        return 2
    command = build_command(args)
    print("dataset preflight: ok (%s, %d BVHs)" % (args.dataset, len(bvh_files)))
    print("working directory: <user-supplied source root>")
    print("command: %s" % shlex.join(command))
    if not args.execute:
        print("dry-run only; pass --execute after reviewing output/copy effects")
        return 0
    return subprocess.call(command, cwd=str(Path(args.source_root).expanduser()))


if __name__ == "__main__":
    raise SystemExit(main())
