#!/usr/bin/env python3
"""Smoke-check the TorchIO CLI using temporary synthetic NIfTI data."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny temporary NIfTI fixture and run safe TorchIO CLI "
            "help/info/convert checks. Falls back to python -m torchio.cli "
            "when the torchio executable is unavailable."
        ),
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Do not delete the temporary fixture directory after the check.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the commands that would be run without executing them.",
    )
    parser.add_argument(
        "--skip-convert",
        action="store_true",
        help="Skip the NIfTI conversion check and only run help/info commands.",
    )
    return parser.parse_args()


def make_fixture(directory: Path) -> Path:
    try:
        import nibabel as nib
        import numpy as np
    except ImportError as exc:
        raise SystemExit(
            "This smoke check needs nibabel and numpy to create a tiny fixture. "
            "Install TorchIO's base dependencies and retry."
        ) from exc

    data = np.arange(8 * 8 * 8, dtype=np.float32).reshape(8, 8, 8)
    image = nib.Nifti1Image(data, np.eye(4))
    path = directory / "tiny.nii.gz"
    nib.save(image, path)
    return path


def resolve_torchio_command() -> list[str]:
    executable = shutil.which("torchio")
    if executable is not None:
        return [executable]
    return [sys.executable, "-m", "torchio.cli"]


def run_command(label: str, command: list[str]) -> CommandResult:
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return CommandResult(
        label=label,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def sanitize_text(text: str) -> str:
    text = re.sub(r"/\S*/torchio/cli\.py", "torchio", text)
    text = re.sub(r"\S*torchio-cli-smoke-[^\s]+/tiny\.nii\.gz", "<temporary-input.nii.gz>", text)
    text = re.sub(r"\S*torchio-cli-smoke-[^\s]+/tiny-converted\.nii", "<temporary-output.nii>", text)
    return text.replace(sys.executable, "python")


def display_command(command: list[str]) -> str:
    if len(command) >= 3 and command[1:3] == ["-m", "torchio.cli"]:
        display = "torchio " + " ".join(str(part) for part in command[3:])
    elif command and command[0].endswith("torchio"):
        display = "torchio " + " ".join(str(part) for part in command[1:])
    else:
        display = "torchio " + " ".join(str(part) for part in command[1:])
    return sanitize_text(display)


def print_command(command: list[str]) -> None:
    print("$ " + display_command(command))


def report_result(result: CommandResult) -> bool:
    print(f"\n[{result.label}]")
    print_command(result.command)
    if result.stdout.strip():
        print("stdout:")
        print(sanitize_text(result.stdout.rstrip()))
    if result.stderr.strip():
        print("stderr:", file=sys.stderr)
        print(sanitize_text(result.stderr.rstrip()), file=sys.stderr)
    if result.returncode != 0:
        print(f"FAILED with exit code {result.returncode}", file=sys.stderr)
        return False
    print("OK")
    return True


def build_commands(base: list[str], input_path: Path, output_path: Path, skip_convert: bool) -> list[tuple[str, list[str]]]:
    commands: list[tuple[str, list[str]]] = [
        ("version", [*base, "--version"]),
        ("top-level help", [*base, "--help"]),
        ("info help", [*base, "info", "--help"]),
        ("convert help", [*base, "convert", "--help"]),
        ("info tiny fixture", [*base, "info", str(input_path)]),
    ]
    if not skip_convert:
        commands.append(
            (
                "convert tiny fixture",
                [*base, "convert", str(input_path), str(output_path)],
            ),
        )
    return commands


def main() -> int:
    args = parse_args()
    temp_dir = Path(tempfile.mkdtemp(prefix="torchio-cli-smoke-"))
    try:
        input_path = temp_dir / "tiny.nii.gz"
        output_path = temp_dir / "tiny-converted.nii"
        base = resolve_torchio_command()
        commands = build_commands(base, input_path, output_path, args.skip_convert)

        print("TorchIO CLI command base: torchio")
        print("Temporary fixture: created in a temporary directory")

        if args.print_only:
            for _label, command in commands:
                print_command(command)
            print("Print-only mode: no commands executed and no fixture created.")
            return 0

        input_path = make_fixture(temp_dir)

        ok = True
        for label, command in commands:
            ok = report_result(run_command(label, command)) and ok

        if not args.skip_convert:
            if output_path.exists() and output_path.stat().st_size > 0:
                print("\nConverted fixture exists and is non-empty")
            else:
                print("\nConverted fixture was not created", file=sys.stderr)
                ok = False
        return 0 if ok else 1
    finally:
        if args.keep_temp:
            print(f"Kept temporary directory: {temp_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
