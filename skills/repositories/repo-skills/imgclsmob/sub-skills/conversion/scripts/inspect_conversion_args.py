#!/usr/bin/env python3
"""Validate conversion plans without importing a framework or doing conversion I/O.

The repository's conversion entrypoint imports backends before it can inspect a
plan.  This bundled checker deliberately does not import that entrypoint or any
ML package.  It validates the dispatched edge and conservative policy gates;
it never opens a checkpoint, creates an output, writes a log, or uses a network.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Iterable


SOURCE_FRAMEWORKS = ("gluon", "pytorch", "mxnet", "tensorflow", "tf2")
DESTINATION_FRAMEWORKS = (
    "gluon",
    "pytorch",
    "chainer",
    "keras",
    "tensorflow",
    "tf2",
    "tfl",
)

# This is the dispatch table, not a claim that every framework package can
# serialize every other framework's weights.
DISPATCH = {
    ("gluon", "gluon"): "convert_gl2gl",
    ("gluon", "pytorch"): "convert_gl2pt",
    ("gluon", "chainer"): "convert_gl2ch",
    ("gluon", "keras"): "convert_gl2ke",
    ("gluon", "tensorflow"): "convert_gl2tf",
    ("gluon", "tf2"): "convert_gl2tf2",
    ("pytorch", "pytorch"): "convert_pt2pt",
    ("pytorch", "gluon"): "convert_pt2gl",
    ("mxnet", "gluon"): "convert_mx2gl",
    ("tensorflow", "tensorflow"): "convert_tf2tf",
    ("tensorflow", "gluon"): "convert_tf2gl",
    ("tf2", "tfl"): "convert_tf22tfl",
}

# These are inspector-only controls.  They are not flags accepted by
# convert_models.py itself.
INSPECTOR_POLICIES = (
    "--cpu-only",
    "--check-files",
    "--entrypoint",
    "--output-dir",
    "--input-shape",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List or validate convert_models.py framework arguments without "
            "loading, converting, downloading, or creating files."
        )
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print exact labels and dispatched source/destination edges",
    )
    parser.add_argument("--src-fwk", help="source framework label")
    parser.add_argument("--dst-fwk", help="destination framework label")
    parser.add_argument("--src-model", help="source model identifier")
    parser.add_argument("--dst-model", help="destination model identifier")
    parser.add_argument("--src-params", help="source checkpoint or MXNet prefix")
    parser.add_argument("--dst-params", help="destination artifact path")
    parser.add_argument(
        "--load-ignore-extra",
        action="store_true",
        help="record the PyTorch source extra-key loading option",
    )
    parser.add_argument(
        "--remove-module",
        action="store_true",
        help="record the PyTorch DataParallel module-prefix option",
    )
    parser.add_argument("--src-num-classes", type=int, default=1000)
    parser.add_argument("--src-in-channels", type=int, default=3)
    parser.add_argument("--dst-num-classes", type=int, default=1000)
    parser.add_argument("--dst-in-channels", type=int, default=3)
    # The real parser accepts an arbitrary string.  The conversion code treats
    # exactly "image" as image input and every other value as its audio branch;
    # the inspector applies the documented image/audio policy below.
    parser.add_argument("--model-type", default="image")
    parser.add_argument("--save-dir", default="")
    parser.add_argument("--logging-file-name", default="train.log")
    parser.add_argument(
        "--cpu-only",
        action="store_true",
        help="apply the conservative CPU verification gate (inspector only)",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="check that a local source checkpoint/prefix exists",
    )
    parser.add_argument(
        "--entrypoint",
        choices=("convert_models", "tf2-example"),
        default="convert_models",
        help=(
            "policy mode; use tf2-example for local TF2-to-TFLite input "
            "instead of the pretrained convert_models branch"
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="existing output directory for the local TF2-to-TFLite example (inspector only)",
    )
    parser.add_argument(
        "--input-shape",
        nargs="+",
        type=int,
        help="custom TF2 example shape; rejected as unverified in this snapshot",
    )
    return parser


def _print_list() -> None:
    print("supported source labels: " + ", ".join(SOURCE_FRAMEWORKS))
    print("supported destination labels: " + ", ".join(DESTINATION_FRAMEWORKS))
    print("TF1 label: tensorflow (not tf1)")
    print("TF2 label: tf2")
    print("TFLite label: tfl")
    print("dispatched edges:")
    for (source, destination), function in DISPATCH.items():
        print("  {} -> {} ({})".format(source, destination, function))
    print("unsupported as CLI sources: chainer, keras")
    print("no dispatched destination: mxnet")
    print("inspector-only policies: " + ", ".join(INSPECTOR_POLICIES))


def _require(value: str | None, flag: str, errors: list[str]) -> None:
    if not value:
        errors.append("missing required plan flag {}".format(flag))


def _existing_checkpoint(path_text: str, source: str) -> bool:
    """Check only filesystem presence; never open or parse the checkpoint."""
    path = Path(path_text).expanduser()
    if source != "mxnet":
        return path.is_file()

    # mx.model.load_checkpoint receives a prefix and appends the epoch.  A
    # symbol file plus the epoch-0000 parameter file is the normal pair.
    symbol = Path(str(path) + "-symbol.json")
    epoch_params = Path(str(path) + "-0000.params")
    return symbol.is_file() and epoch_params.is_file()


def _positive_args(args: argparse.Namespace, errors: list[str]) -> None:
    for name in (
        "src_num_classes",
        "src_in_channels",
        "dst_num_classes",
        "dst_in_channels",
    ):
        if getattr(args, name) <= 0:
            errors.append("--{} must be a positive integer".format(name.replace("_", "-")))


def _validate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    notes: list[str] = []

    required_plan_flags = (
        (args.src_fwk, "--src-fwk"),
        (args.dst_fwk, "--dst-fwk"),
        (args.src_model, "--src-model"),
        (args.dst_model, "--dst-model"),
        (args.src_params, "--src-params"),
        (args.dst_params, "--dst-params"),
    )
    for value, flag in required_plan_flags:
        _require(value, flag, errors)

    if args.src_fwk and args.src_fwk not in SOURCE_FRAMEWORKS:
        if args.src_fwk in ("tf1", "tensorflow1", "tensorflow-1"):
            errors.append(
                "use --src-fwk tensorflow for legacy TensorFlow 1.x; do not use {}".format(
                    args.src_fwk
                )
            )
        else:
            errors.append(
                "unsupported --src-fwk {!r}; use --list for exact choices".format(args.src_fwk)
            )
    if args.dst_fwk and args.dst_fwk not in DESTINATION_FRAMEWORKS:
        if args.dst_fwk in ("tf1", "tensorflow1", "tensorflow-1"):
            errors.append(
                "use --dst-fwk tensorflow for legacy TensorFlow 1.x; do not use {}".format(
                    args.dst_fwk
                )
            )
        else:
            errors.append(
                "unsupported --dst-fwk {!r}; use --list for exact choices".format(args.dst_fwk)
            )

    _positive_args(args, errors)

    edge = (args.src_fwk, args.dst_fwk)
    if args.src_fwk in SOURCE_FRAMEWORKS and args.dst_fwk in DESTINATION_FRAMEWORKS:
        if edge not in DISPATCH:
            errors.append(
                "unsupported conversion edge {} -> {}; use --list for dispatched edges".format(
                    args.src_fwk, args.dst_fwk
                )
            )
        else:
            notes.append("dispatch: {}".format(DISPATCH[edge]))

    if args.model_type not in ("image", "audio"):
        errors.append(
            "--model-type must be image or audio for a safe plan; the source "
            "parser accepts any string but treats non-image values as audio"
        )

    if args.src_params and args.dst_params:
        source_path = os.path.normcase(os.path.abspath(os.path.expanduser(args.src_params)))
        destination_path = os.path.normcase(os.path.abspath(os.path.expanduser(args.dst_params)))
        if source_path == destination_path:
            errors.append("--src-params and --dst-params must not name the same path")

    if args.input_shape:
        if args.entrypoint != "tf2-example":
            errors.append("--input-shape is inspector-only and requires --entrypoint tf2-example")
        else:
            errors.append(
                "custom --input-shape is blocked/unverified: the local example "
                "declares one int but later treats it as a four-value sequence"
            )

    if args.entrypoint == "tf2-example":
        if edge != ("tf2", "tfl"):
            errors.append("--entrypoint tf2-example is only valid for tf2 -> tfl")
        if args.output_dir:
            output_dir = Path(args.output_dir).expanduser()
            if args.check_files and not output_dir.is_dir():
                errors.append("local TF2 example --output-dir is not an existing directory")
            notes.append("local example output: <output-dir>/<src-model>.tflite")
        if args.dst_params:
            notes.append("--dst-params is the planned artifact path; the local example writes under --output-dir")
        else:
            notes.append("local example has no --output-dir; it converts in memory without writing a TFLite file")
        notes.append("local-input mode: map --src-params to the example's --input flag")
    elif args.output_dir:
        errors.append("--output-dir is inspector-only and requires --entrypoint tf2-example")
    elif edge == ("tf2", "tfl"):
        errors.append(
            "blocked no-network plan: convert_models.py tf2 -> tfl uses "
            "use_pretrained=True with an empty source path; use --entrypoint tf2-example"
        )
        notes.append(
            "the local example writes <output-dir>/<model>.tflite and requires "
            "an already existing output directory"
        )

    if args.cpu_only and edge == ("gluon", "pytorch"):
        errors.append(
            "blocked CPU-only Gluon -> PyTorch: focused conversion tests use "
            "mx.gpu(0) and PyTorch .cuda(); CPU support is unverified"
        )
        notes.append(
            "checklist: matching model/classes/channels, local .params and .pth, "
            "compatible CUDA backends, then obtain separate CPU smoke-test approval"
        )

    if args.load_ignore_extra and args.src_fwk != "pytorch":
        notes.append("--load-ignore-extra is accepted by the parser but ignored unless the source is PyTorch")
    if args.remove_module and args.src_fwk != "pytorch":
        notes.append("--remove-module is accepted by the parser but ignored unless the source is PyTorch")
    if args.load_ignore_extra and args.remove_module and args.src_fwk == "pytorch":
        notes.append("PyTorch load-ignore-extra takes precedence; remove-module is not used in that branch")

    if args.src_fwk == "tensorflow" or args.dst_fwk == "tensorflow":
        notes.append("TensorFlow 1.x graph/session path selected; do not substitute tf2")
    if args.src_fwk == "tf2" or args.dst_fwk == "tf2" or args.dst_fwk == "tfl":
        notes.append("TensorFlow 2.x/Keras or TFLite path selected; backend installation is not performed")
    if args.model_type in ("image", "audio") and args.dst_fwk != "tf2":
        notes.append("--model-type is ignored by the conversion code unless the destination is tf2")
    if args.src_fwk == "tf2" and args.dst_fwk == "tfl" and args.entrypoint == "convert_models":
        notes.append("--src-params is ignored by this pretrained convert_models branch")

    if args.check_files and args.src_params and args.src_fwk in SOURCE_FRAMEWORKS:
        if edge == ("tf2", "tfl") and args.entrypoint == "convert_models":
            notes.append("source checkpoint check skipped because convert_models tf2 -> tfl ignores --src-params")
        elif not _existing_checkpoint(args.src_params, args.src_fwk):
            errors.append(
                "source checkpoint/prefix does not exist for --src-params {!r}".format(args.src_params)
            )
        else:
            notes.append("source checkpoint/prefix exists (not opened)")
    elif args.src_params and args.src_fwk == "mxnet":
        notes.append("MXNet source is interpreted as an epoch-0 checkpoint prefix; existence check is opt-in")

    print("plan:")
    print("  source: {} model={}".format(args.src_fwk or "<missing>", args.src_model or "<missing>"))
    print("  destination: {} model={}".format(args.dst_fwk or "<missing>", args.dst_model or "<missing>"))
    print("  source checkpoint: {}".format(args.src_params or "<missing>"))
    print("  destination artifact: {}".format(args.dst_params or "<missing>"))
    print("  entrypoint policy: {}".format(args.entrypoint))
    print("  model-type: {}".format(args.model_type))
    print("  side effects: none (no imports, loads, conversion, writes, or network)")

    for note in notes:
        print("  note: " + note)
    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        print("status: BLOCKED", file=sys.stderr)
        return 2

    print("status: VALID ARGUMENT PLAN")
    print("next: execute only after backend and model-loading checks pass")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.list:
        _print_list()
        return 0
    return _validate(args)


if __name__ == "__main__":
    raise SystemExit(main())
