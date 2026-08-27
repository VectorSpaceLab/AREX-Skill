#!/usr/bin/env python3
"""Safe help and fixture checker for the DreamerV2 plotting interface.

This module intentionally does not import DreamerV2, pandas, Matplotlib, or
files from a source checkout. It validates the directory/JSONL contract before
the real renderer is invoked and can print a renderer command.
"""

import argparse
import json
import pathlib
import runpy
import shlex
import sys


DEFAULT_BASELINES = ("d4pg", "rainbow_sticky", "human_gamer", "impala")


def exact_bool(value):
    if value not in ("False", "True"):
        raise argparse.ArgumentTypeError("expected exactly True or False")
    return value == "True"


def parser():
    p = argparse.ArgumentParser(
        description=(
            "Check DreamerV2 task/method/seed JSONL layout and show the "
            "dependency-free plotting CLI contract. This does not render."
        )
    )
    p.add_argument("--indir", nargs="+", type=pathlib.Path, default=[],
                   help="run roots containing task/method/seed/metrics.jsonl")
    p.add_argument("--indir-prefix", type=pathlib.Path,
                   help="prefix each input root after parsing")
    p.add_argument("--outdir", type=pathlib.Path,
                   help="plot destination (required by the real renderer)")
    p.add_argument("--subdir", type=exact_bool, default=True,
                   help="real renderer appends first input basename (True/False)")
    p.add_argument("--xaxis", default="step", help="JSONL x column")
    p.add_argument("--yaxis", default="eval_return", help="JSONL y column")
    p.add_argument("--xmult", type=float, default=1)
    p.add_argument("--maxval", type=float, default=0)
    p.add_argument("--tasks", nargs="+", default=[r".*"])
    p.add_argument("--methods", nargs="+", default=[r".*"])
    p.add_argument("--baselines", nargs="+", default=list(DEFAULT_BASELINES))
    p.add_argument("--prefix", type=exact_bool, default=False)
    p.add_argument("--bins", type=float, default=-1)
    p.add_argument("--agg", default="std1")
    p.add_argument("--size", nargs=2, type=float, default=[2.5, 2.3])
    p.add_argument("--dpi", type=int, default=80)
    p.add_argument("--cols", type=int, default=6)
    p.add_argument("--xlim", nargs=2, type=float)
    p.add_argument("--ylim", nargs=2, type=float)
    p.add_argument("--ylimticks", type=exact_bool, default=True)
    p.add_argument("--xlabel")
    p.add_argument("--ylabel")
    p.add_argument("--xticks", type=int, default=6)
    p.add_argument("--yticks", type=int, default=5)
    p.add_argument("--labels", nargs="+",
                   help="even-length OLD NEW label pairs")
    p.add_argument("--palette", nargs="+", default=["contrast"])
    p.add_argument("--legendcols", type=int, default=4)
    p.add_argument("--colors", nargs="+",
                   help="even-length METHOD COLOR pairs")
    p.add_argument("--add", nargs="+", default=["auto", "seeds"])
    p.add_argument("--validate-layout", action="store_true",
                   help="check paths, JSONL, and selected columns")
    p.add_argument("--print-command", action="store_true",
                   help="print a corresponding real module invocation")
    p.add_argument("--renderer-help", action="store_true",
                   help="run installed dreamerv2 plot --help safely")
    p.add_argument("--render", nargs=argparse.REMAINDER,
                   help="forward remaining flags to the installed plot renderer")
    return p


def check_pairs(parser_obj, values, name):
    if values is not None and len(values) % 2:
        parser_obj.error("--{} requires an even number of values".format(name))


def effective_indirs(args):
    prefix = args.indir_prefix.expanduser() if args.indir_prefix else None
    roots = [path.expanduser() for path in args.indir]
    if prefix:
        roots = [prefix / root for root in roots]
    return roots


def read_jsonl(path):
    """Return (records, errors, trailing_invalid), without third-party deps."""
    records = []
    errors = []
    trailing_invalid = False
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeError) as exc:
        return [], [str(exc)], False
    for index, line in enumerate(lines):
        if not line.strip():
            if index != len(lines) - 1:
                errors.append("blank line {}".format(index + 1))
            continue
        try:
            value = json.loads(line)
        except Exception as exc:  # Match the renderer's tolerant final line.
            if index == len(lines) - 1:
                trailing_invalid = True
                continue
            errors.append("invalid JSON line {}: {}".format(index + 1, exc))
            continue
        if not isinstance(value, dict):
            errors.append("line {} is not a JSON object".format(index + 1))
            continue
        records.append(value)
    return records, errors, trailing_invalid


def validate(roots, xaxis, yaxis):
    total = valid = 0
    empty = layout = invalid = missing = 0
    keys = set()
    for root in roots:
        if not root.exists():
            print("ERROR missing input root: {}".format(root), file=sys.stderr)
            invalid += 1
            continue
        if not root.is_dir():
            print("ERROR input is not a directory: {}".format(root), file=sys.stderr)
            invalid += 1
            continue
        files = sorted(root.rglob("*.jsonl"))
        if not files:
            print("WARNING no JSONL files below {}".format(root))
        for path in files:
            total += 1
            relative = path.relative_to(root).parts
            if len(relative) != 4:
                layout += 1
                print("ERROR layout (need task/method/seed/file): {}".format(path))
                continue
            records, errors, trailing = read_jsonl(path)
            if not records:
                empty += 1
                print("WARNING empty run: {}".format(path))
                continue
            if errors:
                invalid += 1
                print("ERROR invalid run {}: {}".format(path, "; ".join(errors)))
                continue
            valid += 1
            file_keys = set().union(*(record.keys() for record in records))
            keys.update(file_keys)
            if xaxis not in file_keys or yaxis not in file_keys:
                missing += 1
                print("WARNING missing {} or {}: {}".format(xaxis, yaxis, path))
            if trailing:
                print("WARNING ignored incomplete final line: {}".format(path))
    print("Checked {} JSONL file(s); valid={}, empty={}, layout_errors={}, "
          "invalid={}, missing_selected_columns={}".format(
              total, valid, empty, layout, invalid, missing))
    print("Observed keys: {}".format(", ".join(sorted(keys)) if keys else "<none>"))
    return 0 if valid and not layout and not invalid else 1


def run_renderer(arguments):
    """Run plot.py from the installed package, without a checkout path.

    The legacy module imports a top-level ``common`` alias. Add the installed
    package directory to sys.path and use runpy so the alias resolves without
    assuming the caller's cwd or the repository layout.
    """
    try:
        import dreamerv2
    except ImportError as exc:
        print("ERROR dreamerv2 is not installed: {}".format(exc), file=sys.stderr)
        return 1
    package_root = pathlib.Path(next(iter(dreamerv2.__path__))).resolve()
    plot_file = package_root / "common" / "plot.py"
    if not plot_file.is_file():
        print("ERROR installed plot module not found: {}".format(plot_file),
              file=sys.stderr)
        return 1
    sys.path.insert(0, str(package_root))
    sys.argv = [str(plot_file)] + list(arguments)
    try:
        runpy.run_path(str(plot_file), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def renderer_help():
    """Delegate only --help to the installed package module."""
    return run_renderer(["--help"])


def print_command(args, roots):
    if args.outdir is None:
        print("ERROR --print-command requires --outdir", file=sys.stderr)
        return 1
    outdir = args.outdir.expanduser()
    if args.subdir:
        outdir = outdir / roots[0].stem
    command = [sys.executable, str(pathlib.Path(__file__).resolve()), "--render",
               "--indir"]
    command.extend(str(root) for root in roots)
    command.extend(["--outdir", str(outdir), "--subdir", "False"])
    command.extend(["--xaxis", args.xaxis, "--yaxis", args.yaxis])
    command.extend(["--bins", str(args.bins), "--agg", args.agg])
    if args.prefix:
        command.extend(["--prefix", "True"])
    print(shlex.join(command))
    return 0


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if (args.validate_layout or args.print_command) and not args.indir:
        p.error("--indir is required for validation or command printing")
    check_pairs(p, args.labels, "labels")
    check_pairs(p, args.colors, "colors")
    roots = effective_indirs(args)
    status = 0
    if args.validate_layout:
        status = validate(roots, args.xaxis, args.yaxis)
    if args.print_command:
        status = max(status, print_command(args, roots))
    if args.renderer_help:
        status = max(status, renderer_help())
    if args.render is not None:
        status = max(status, run_renderer(args.render))
    if (not args.validate_layout and not args.print_command and
            not args.renderer_help and args.render is None):
        print("No validation requested; use --help, --validate-layout, "
              "--print-command, --renderer-help, or --render.")
    return status


if __name__ == "__main__":
    sys.exit(main())
