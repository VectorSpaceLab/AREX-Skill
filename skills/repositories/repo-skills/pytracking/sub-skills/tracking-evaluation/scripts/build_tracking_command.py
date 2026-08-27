#!/usr/bin/env python3
"""Build, but never execute, PyTracking tracking/evaluation commands.

The emitted command targets PyTracking's public run scripts in a user's checkout.
This helper is intentionally side-effect free: it validates arguments, prints a
shell command, and exits.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from typing import Iterable, List, Sequence

DATASET_ALIASES = (
    "avist",
    "dv2016_val",
    "dv2017_test_chal",
    "dv2017_test_dev",
    "dv2017_val",
    "got10k_ltrval",
    "got10k_test",
    "got10k_val",
    "got10kvos_val",
    "lagot",
    "lagot_sot_mode",
    "lasot",
    "lasot_extension_subset",
    "lasot_train",
    "lasotvos",
    "nfs",
    "otb",
    "oxuva_dev",
    "oxuva_test",
    "tpl",
    "tpl_nootb",
    "trackingnet",
    "trackingnetvos",
    "uav",
    "vot",
    "yt2018_jjval",
    "yt2018_valid_all",
    "yt2019_jjval",
    "yt2019_jjval_all",
    "yt2019_test",
    "yt2019_valid",
    "yt2019_valid_all",
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTTED_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


def module_part(value: str) -> str:
    if not _IDENTIFIER_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a Python module/function-safe identifier. "
            "Use names such as dimp, dimp50, default, myexperiments."
        )
    return value


def dotted_module(value: str) -> str:
    if not _DOTTED_IDENTIFIER_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a safe dotted Python module name."
        )
    return value


def dataset_alias(value: str) -> str:
    alias = value.lower()
    if alias not in DATASET_ALIASES:
        allowed = ", ".join(DATASET_ALIASES)
        raise argparse.ArgumentTypeError(
            f"unknown dataset alias {value!r}. Known aliases: {allowed}"
        )
    return alias


def nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def port_number(value: str) -> int:
    parsed = nonnegative_int(value)
    if parsed < 1 or parsed > 65535:
        raise argparse.ArgumentTypeError("port must be in [1, 65535]")
    return parsed


def parse_optional_box(values: Sequence[str] | None) -> List[float] | None:
    if values is None:
        return None
    pieces: List[str] = []
    for value in values:
        pieces.extend(part for part in value.split(",") if part != "")
    if len(pieces) != 4:
        raise argparse.ArgumentTypeError(
            "optional_box must contain exactly four numbers: x y w h"
        )
    try:
        return [float(part) for part in pieces]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "optional_box must contain exactly four numeric values: x y w h"
        ) from exc


def format_number(value: float) -> str:
    return f"{value:g}"


def join_entry(entry_root: str, script_name: str) -> str:
    root = entry_root.rstrip("/")
    if root in ("", "."):
        return script_name
    return f"{root}/{script_name}"


def add_common_arguments(parser: argparse.ArgumentParser, *, needs_tracker: bool = True) -> None:
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable to place at the front of the emitted command (default: python).",
    )
    parser.add_argument(
        "--entry-root",
        default="pytracking",
        help=(
            "Directory containing PyTracking run_*.py entry scripts, relative to the "
            "eventual execution directory or absolute in the user's environment "
            "(default: pytracking)."
        ),
    )
    parser.add_argument(
        "--debug",
        type=nonnegative_int,
        default=0,
        help="PyTracking debug level to emit (default: 0).",
    )
    if needs_tracker:
        parser.add_argument("--tracker", required=True, type=module_part, help="Tracker module name, e.g. dimp.")
        parser.add_argument("--param", required=True, type=module_part, help="Parameter module name, e.g. dimp50.")


def add_visdom_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--visdom",
        choices=("default", "on", "off"),
        default="default",
        help=(
            "Visdom CLI emission for dataset/webcam modes. 'default' omits native flags; "
            "'on' emits --use_visdom True; 'off' emits the empty-string workaround needed "
            "by PyTracking's type=bool parser."
        ),
    )
    parser.add_argument("--visdom-server", default="127.0.0.1", help="Visdom server host to emit when Visdom flags are emitted.")
    parser.add_argument("--visdom-port", type=port_number, default=8097, help="Visdom port to emit when Visdom flags are emitted.")


def add_output_arguments(parser: argparse.ArgumentParser) -> None:
    """Allow output-format flags either before or after the MODE token."""
    parser.add_argument("--as-json", action="store_true", default=argparse.SUPPRESS, help="Emit JSON with argv, command, and notes.")
    parser.add_argument("--explain", action="store_true", default=argparse.SUPPRESS, help="Print explanatory notes after the command.")


def append_visdom(argv: List[str], args: argparse.Namespace, notes: List[str]) -> None:
    if args.visdom == "default":
        return
    if args.visdom == "off":
        # The upstream run scripts declare argparse type=bool. Strings such as
        # "False" and "0" become True. Passing an empty string is the only CLI
        # way to produce bool('') == False; programmatic API control is cleaner.
        argv.extend(["--use_visdom", ""])
        notes.append(
            "Visdom off uses an empty-string CLI workaround because PyTracking's native parser treats most strings, including 'False', as True. Prefer debug 0 or the Python API for reliable no-Visdom runs."
        )
    else:
        argv.extend([
            "--use_visdom",
            "True",
            "--visdom_server",
            args.visdom_server,
            "--visdom_port",
            str(args.visdom_port),
        ])


def build_dataset(args: argparse.Namespace) -> tuple[List[str], List[str]]:
    notes = [
        "Command only; verify local.py dataset paths, network_path/checkpoints, and runtime budget before running.",
    ]
    argv = [
        args.python,
        join_entry(args.entry_root, "run_tracker.py"),
        args.tracker,
        args.param,
        "--dataset_name",
        args.dataset,
        "--debug",
        str(args.debug),
        "--threads",
        str(args.threads),
    ]
    if args.sequence is not None:
        argv.extend(["--sequence", args.sequence])
    if args.runid is not None:
        argv.extend(["--runid", str(args.runid)])
    append_visdom(argv, args, notes)
    if args.sequence is None:
        notes.append("No sequence was specified, so the emitted command targets the full dataset alias.")
    return argv, notes


def build_video(args: argparse.Namespace) -> tuple[List[str], List[str]]:
    notes = [
        "Command only; video mode opens an OpenCV GUI window when run.",
        "The native video CLI has no Visdom on/off flag; use debug 0 or the Python API if you need strict no-Visdom behavior.",
    ]
    box = parse_optional_box(args.optional_box)
    argv = [
        args.python,
        join_entry(args.entry_root, "run_video.py"),
        args.tracker,
        args.param,
        args.videofile,
        "--debug",
        str(args.debug),
    ]
    if box is not None:
        argv.extend(["--optional_box", *(format_number(v) for v in box)])
    if args.save_results:
        argv.append("--save_results")
        notes.append("--save_results writes video_<stem>_<object-id>.txt files under the configured results path.")
    return argv, notes


def build_webcam(args: argparse.Namespace) -> tuple[List[str], List[str]]:
    notes = [
        "Command only; webcam mode opens camera index 0 and an OpenCV GUI window when run.",
    ]
    argv = [
        args.python,
        join_entry(args.entry_root, "run_webcam.py"),
        args.tracker,
        args.param,
        "--debug",
        str(args.debug),
    ]
    append_visdom(argv, args, notes)
    return argv, notes


def build_experiment(args: argparse.Namespace) -> tuple[List[str], List[str]]:
    notes = [
        "Command only; the experiment function must return (trackers, dataset).",
        "Dataset aliases and tracker lists are selected inside the experiment function, not on this CLI.",
    ]
    argv = [
        args.python,
        join_entry(args.entry_root, "run_experiment.py"),
        args.experiment_module,
        args.experiment_name,
        "--debug",
        str(args.debug),
        "--threads",
        str(args.threads),
    ]
    return argv, notes


def emit(argv: Sequence[str], notes: Sequence[str], args: argparse.Namespace) -> int:
    command = shlex.join(list(argv))
    if args.as_json:
        print(json.dumps({"mode": args.mode, "argv": list(argv), "command": command, "notes": list(notes)}, indent=2))
    else:
        print(command)
        if args.explain:
            print("\nNotes:")
            for note in notes:
                print(f"- {note}")
        elif notes:
            # Preserve stdout as a copy-pastable command while still surfacing safety notes.
            for note in notes:
                print(f"note: {note}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build PyTracking tracking/evaluation commands without executing them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--list-datasets", action="store_true", help="Print supported dataset aliases and exit.")
    parser.add_argument("--as-json", action="store_true", help="Emit JSON with argv, command, and notes.")
    parser.add_argument("--explain", action="store_true", help="Print explanatory notes after the command.")

    subparsers = parser.add_subparsers(dest="mode", metavar="MODE")

    dataset = subparsers.add_parser("dataset", help="Build a run_tracker.py command.")
    add_common_arguments(dataset)
    add_visdom_arguments(dataset)
    add_output_arguments(dataset)
    dataset.add_argument("--dataset", type=dataset_alias, default="otb", help="Dataset alias for --dataset_name.")
    dataset.add_argument("--sequence", help="Optional sequence name or integer index. Omit for full dataset.")
    dataset.add_argument("--runid", type=nonnegative_int, help="Optional run id; PyTracking uses zero-padded result-directory suffixes.")
    dataset.add_argument("--threads", type=nonnegative_int, default=0, help="Multiprocessing worker count; 0 means sequential.")
    dataset.set_defaults(builder=build_dataset)

    video = subparsers.add_parser("video", help="Build a run_video.py command.")
    add_common_arguments(video)
    add_output_arguments(video)
    video.add_argument("--videofile", required=True, help="Path to the eventual video file; not checked by this helper.")
    video.add_argument(
        "--optional-box",
        nargs="+",
        metavar="N",
        help="Initialization box as four numbers x y w h. Comma-separated form is also accepted.",
    )
    video.add_argument("--save-results", action="store_true", help="Emit --save_results for bounding-box text output.")
    video.set_defaults(builder=build_video)

    webcam = subparsers.add_parser("webcam", help="Build a run_webcam.py command.")
    add_common_arguments(webcam)
    add_visdom_arguments(webcam)
    add_output_arguments(webcam)
    webcam.set_defaults(builder=build_webcam)

    experiment = subparsers.add_parser("experiment", help="Build a run_experiment.py command.")
    add_common_arguments(experiment, needs_tracker=False)
    add_output_arguments(experiment)
    experiment.add_argument("--experiment-module", required=True, type=dotted_module, help="Experiment module below pytracking.experiments, without .py.")
    experiment.add_argument("--experiment-name", required=True, type=module_part, help="Experiment function name.")
    experiment.add_argument("--threads", type=nonnegative_int, default=0, help="Multiprocessing worker count; 0 means sequential.")
    experiment.set_defaults(builder=build_experiment)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list_datasets:
        for alias in DATASET_ALIASES:
            print(alias)
        return 0

    if not getattr(args, "mode", None):
        parser.error("choose a MODE or pass --list-datasets")

    try:
        command_argv, notes = args.builder(args)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    return emit(command_argv, notes, args)


if __name__ == "__main__":
    raise SystemExit(main())
