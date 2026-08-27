#!/usr/bin/env python3
"""Compile an MJCF/XML model through MuJoCo and save the resolved XML.

The helper keeps a temporary copy of the source file in the same directory so
relative asset references keep resolving while MuJoCo loads the model. The
compiled XML is written to a new file only after the model loads successfully.

Examples:
    python compile_mjcf_model.py input.xml output.xml
    python compile_mjcf_model.py input.xml output.xml --overwrite
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path


def _validate_input_path(raw_path):
    path = Path(raw_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"input file does not exist: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"input path is not a file: {path}")
    return path.resolve()


def _validate_output_path(raw_path, input_path, overwrite):
    path = Path(raw_path).expanduser()
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"output path is a directory: {path}")
    if path.exists() and not overwrite:
        raise FileExistsError(f"output file already exists: {path} (use --overwrite to replace it)")
    if not path.parent.exists():
        raise FileNotFoundError(f"output directory does not exist: {path.parent}")

    resolved = path.resolve(strict=False)
    if resolved == input_path:
        raise ValueError("input and output paths must be different")
    return resolved


def compile_mjcf_model(input_path, output_path):
    import mujoco

    fd, temp_name = tempfile.mkstemp(
        dir=str(input_path.parent),
        prefix=".robosuite_mjcf_",
        suffix=".xml",
    )
    os.close(fd)
    temp_path = Path(temp_name)
    shutil.copyfile(input_path, temp_path)
    try:
        model = mujoco.MjModel.from_xml_path(str(temp_path))
        mujoco.mj_saveLastXML(str(output_path), model)
    finally:
        temp_path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compile an MJCF/XML file through MuJoCo and save the resolved XML."
    )
    parser.add_argument("input_file", help="Path to the source MJCF/XML file.")
    parser.add_argument("output_file", help="Path for the compiled XML output.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output file instead of failing.",
    )
    args = parser.parse_args(argv)

    try:
        input_path = _validate_input_path(args.input_file)
        output_path = _validate_output_path(args.output_file, input_path, args.overwrite)
        compile_mjcf_model(input_path, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Compiled MJCF written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
