#!/usr/bin/env python3
"""Plan a ModelScope custom pipeline scaffold command safely.

This script prints the `modelscope pipeline --action create ...` command that a
user may choose to run separately. It performs argument validation only; it does
not import ModelScope, create directories, write files, download models, train,
or contact the network.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List


def _non_empty(value: str) -> str:
    if value is None or value.strip() == "":
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _python_filename(value: str) -> str:
    value = _non_empty(value)
    name = Path(value).name
    if name in {"", ".", ".."}:
        raise argparse.ArgumentTypeError("filename must be a file name")
    if not name.endswith(".py"):
        raise argparse.ArgumentTypeError("filename must end with .py")
    return value


def build_command(args: argparse.Namespace) -> List[str]:
    return [
        "modelscope",
        "pipeline",
        "--action",
        "create",
        "--tpl_file_path",
        args.tpl_file_path,
        "--save_file_path",
        args.save_file_path,
        "--filename",
        args.filename,
        "--task_name",
        args.task_name,
        "--model_name",
        args.model_name,
        "--preprocessor_name",
        args.preprocessor_name,
        "--pipeline_name",
        args.pipeline_name,
        "--configuration_path",
        args.configuration_path,
    ]


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a safe dry-run command for `modelscope pipeline --action "
            "create`. No files are written."
        )
    )
    parser.add_argument(
        "--tpl_file_path",
        "-tpl",
        default="template.tpl",
        type=_non_empty,
        help=(
            "Template name or path to pass to ModelScope. Default: "
            "template.tpl."
        ),
    )
    parser.add_argument(
        "--save_file_path",
        "-s",
        default="./",
        type=_non_empty,
        help="Directory where the real CLI would write the Python wrapper.",
    )
    parser.add_argument(
        "--filename",
        "-f",
        default="ms_wrapper.py",
        type=_python_filename,
        help="Python wrapper filename; must end with .py.",
    )
    parser.add_argument(
        "--task_name",
        "-t",
        required=True,
        type=_non_empty,
        help="Unique ModelScope task/registry group name.",
    )
    parser.add_argument(
        "--model_name",
        "-m",
        default="MyCustomModel",
        type=_non_empty,
        help="Generated custom model class name.",
    )
    parser.add_argument(
        "--preprocessor_name",
        "-p",
        default="MyCustomPreprocessor",
        type=_non_empty,
        help="Generated custom preprocessor class name.",
    )
    parser.add_argument(
        "--pipeline_name",
        "-pp",
        default="MyCustomPipeline",
        type=_non_empty,
        help="Generated custom pipeline class name.",
    )
    parser.add_argument(
        "--configuration_path",
        "-config",
        default="./",
        type=_non_empty,
        help="Directory where generated code would write configuration.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = build_command(args)
    print("Planned command:")
    print(quote_command(command))
    print()
    print("Safety notes:")
    print("- This planner did not write files or import ModelScope.")
    print("- The real command may create the save directory and wrapper file.")
    print(
        "- Review generated Python before importing it; templates can contain "
        "top-level code."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
