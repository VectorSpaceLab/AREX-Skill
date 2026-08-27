#!/usr/bin/env python3
"""Run one supported GeoSeg repository entry point through a bundled wrapper.

The generated skill cannot assume that the original checkout is the current
working directory. Pass an explicit ``--repo-root`` and a supported entry-point
basename; the wrapper changes into that checkout, exposes it on ``sys.path``,
and forwards the remaining arguments unchanged. It performs no downloads or
writes beyond whatever the selected GeoSeg entry point itself requests.

Example:
    python run_geoseg_entrypoint.py --repo-root /path/to/GeoSeg \
        train_supervision.py --help
"""

import argparse
import os
import runpy
import sys
from pathlib import Path

ENTRYPOINTS = {
    "train_supervision.py",
    "vaihingen_test.py",
    "potsdam_test.py",
    "loveda_test.py",
    "inference_uavid.py",
    "inference_huge_image.py",
}


def parse_wrapper_args(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        add_help=False,
        description="Forward a supported GeoSeg CLI from an explicit checkout.",
    )
    parser.add_argument("--repo-root", required=True, type=Path, help="GeoSeg checkout root")
    parser.add_argument("entrypoint", choices=sorted(ENTRYPOINTS), help="entry-point basename")
    if raw in (["--wrapper-help"], ["--help"]):
        parser.print_help()
        return None, None, None
    args, forwarded = parser.parse_known_args(raw)
    return args, forwarded, parser


def main(argv=None):
    args, forwarded, _ = parse_wrapper_args(argv)
    if args is None:
        return 0
    repo_root = args.repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit("--repo-root is not a directory: {}".format(repo_root))
    entrypoint = repo_root / args.entrypoint
    if not entrypoint.is_file():
        raise SystemExit("entry point is absent under --repo-root: {}".format(entrypoint))

    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    try:
        os.chdir(str(repo_root))
        sys.path.insert(0, str(repo_root))
        sys.argv = [str(entrypoint)] + forwarded
        runpy.run_path(str(entrypoint), run_name="__main__")
    finally:
        sys.argv = old_argv
        if sys.path and sys.path[0] == str(repo_root):
            sys.path.pop(0)
        os.chdir(str(old_cwd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
