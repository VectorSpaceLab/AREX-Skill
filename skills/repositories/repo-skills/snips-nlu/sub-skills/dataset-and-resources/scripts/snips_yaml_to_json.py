#!/usr/bin/env python3
"""Convert Snips NLU YAML intent/entity documents to JSON without training."""

import argparse
import json
import sys
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(
        description="Convert Snips NLU YAML intent/entity documents to JSON without training."
    )
    parser.add_argument(
        "--language",
        required=True,
        help="Snips NLU dataset language code, for example en, fr, or pt_br.",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON output path. Defaults to stdout. Existing files are not overwritten unless --overwrite is set.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow --output to replace an existing file.",
    )
    parser.add_argument(
        "yaml_files",
        nargs="+",
        help="One or more YAML files containing type: intent and/or type: entity documents.",
    )
    return parser


def check_input_paths(paths):
    checked = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise OSError("YAML input does not exist: {}".format(raw_path))
        if path.is_dir():
            raise OSError("YAML input is a directory: {}".format(raw_path))
        checked.append(path)
    return checked


def check_output_path(output, inputs, overwrite):
    if output is None:
        return None
    path = Path(output)
    if path.exists() and path.is_dir():
        raise OSError("output path is a directory: {}".format(output))
    if path.exists() and not overwrite:
        raise OSError("output file exists; pass --overwrite to replace it: {}".format(output))
    input_resolved = {p.resolve() for p in inputs}
    if path.exists() and path.resolve() in input_resolved:
        raise OSError("refusing to overwrite an input YAML file: {}".format(output))
    if not path.exists() and path.parent and not path.parent.exists():
        raise OSError("output parent directory does not exist: {}".format(path.parent))
    return path


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        yaml_paths = check_input_paths(args.yaml_files)
        output_path = check_output_path(args.output, yaml_paths, args.overwrite)
    except OSError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1

    try:
        from snips_nlu.dataset import Dataset
    except Exception as exc:  # pragma: no cover - environment dependent
        print(
            "Snips NLU Dataset API is unavailable: {}: {}".format(
                type(exc).__name__, exc
            ),
            file=sys.stderr,
        )
        return 3

    try:
        dataset = Dataset.from_yaml_files(args.language, [str(path) for path in yaml_paths])
    except Exception as exc:
        print("conversion failed: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 1

    payload = json.dumps(dataset.json, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output_path is None:
        sys.stdout.write(payload)
    else:
        with output_path.open("w", encoding="utf8") as stream:
            stream.write(payload)
        print("wrote JSON dataset: {}".format(output_path), file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
