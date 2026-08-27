#!/usr/bin/env python3
"""Generate repeat-safe OpenFE quickrun commands without executing them."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def transformation_files(path: Path, recursive: bool) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() != ".json":
            raise SystemExit(f"Transformation file must end in .json: {path}")
        return [path]
    if not path.is_dir():
        raise SystemExit(f"Transformation path does not exist: {path}")
    pattern = "**/*.json" if recursive else "*.json"
    files = sorted(p for p in path.glob(pattern) if p.is_file())
    if not files:
        raise SystemExit(f"No transformation JSON files found under: {path}")
    return files


def safe_stem(path: Path) -> str:
    parts = path.with_suffix("").parts
    return "__".join(part.replace(" ", "_") for part in parts if part not in {".", ""})


def quote_path(path: Path) -> str:
    return shlex.quote(path.as_posix())


def build_command(
    openfe_executable: str,
    transformation: Path,
    output_path: Path,
    work_dir: Path,
    resume: bool,
    log_config: str | None,
) -> str:
    pieces = [shlex.quote(openfe_executable)]
    if log_config:
        pieces.extend(["--log", shlex.quote(log_config)])
    pieces.extend(
        [
            "quickrun",
            quote_path(transformation),
            "-o",
            quote_path(output_path),
            "-d",
            quote_path(work_dir),
        ]
    )
    if resume:
        pieces.append("--resume")
    return " ".join(pieces)


def slurm_script(command: str, job_name: str, slurm_options: list[str]) -> str:
    lines = ["#!/usr/bin/env bash", f"#SBATCH --job-name={job_name}"]
    lines.extend(slurm_options)
    lines.extend(["set -euo pipefail", command])
    return "\n".join(lines)


def detect_duplicates(paths: list[Path], label: str) -> None:
    seen: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in paths:
        key = path.as_posix()
        if key in seen:
            duplicates.append(key)
        else:
            seen[key] = path
    if duplicates:
        joined = "\n".join(f"  - {item}" for item in sorted(set(duplicates)))
        raise SystemExit(f"Duplicate {label} paths would be generated:\n{joined}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan OpenFE transformation JSON files and print repeat-safe quickrun "
            "commands or simple Slurm scripts. This tool never executes commands, "
            "writes job files, submits jobs, downloads data, or creates result directories."
        )
    )
    parser.add_argument(
        "transformations",
        type=Path,
        help="Transformation JSON file or directory containing transformation JSON files.",
    )
    parser.add_argument(
        "--repeats",
        type=positive_int,
        default=3,
        help="Number of repeat commands to print per transformation. Default: 3.",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("results_parallel"),
        help="Root directory to use when constructing result JSON paths.",
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("work_parallel"),
        help="Root directory to use when constructing quickrun work directories.",
    )
    parser.add_argument(
        "--format",
        choices=["commands", "slurm"],
        default="commands",
        help="Print bare shell commands or one Slurm script block per command.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories for JSON files instead of only direct children.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append --resume to every generated quickrun command.",
    )
    parser.add_argument(
        "--log-config",
        help="Optional logging config path to place as global `openfe --log PATH` before quickrun.",
    )
    parser.add_argument(
        "--openfe-executable",
        default="openfe",
        help="Executable name or path for the OpenFE CLI. Default: openfe.",
    )
    parser.add_argument(
        "--slurm-job-prefix",
        default="openfe",
        help="Job-name prefix used when --format slurm is selected.",
    )
    parser.add_argument(
        "--slurm-option",
        action="append",
        default=[],
        help="Additional SBATCH line, for example: --slurm-option '#SBATCH --gres=gpu:1'. Repeatable.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    transformations = transformation_files(args.transformations, args.recursive)

    commands: list[tuple[str, str]] = []
    output_paths: list[Path] = []
    work_dirs: list[Path] = []

    for transformation in transformations:
        relative_stem = safe_stem(
            transformation.relative_to(args.transformations)
            if args.transformations.is_dir() and transformation.is_relative_to(args.transformations)
            else Path(transformation.stem)
        )
        for repeat in range(args.repeats):
            output_path = args.results_root / f"results_{repeat}" / f"{relative_stem}.json"
            work_dir = args.work_root / f"work_{repeat}" / relative_stem
            output_paths.append(output_path)
            work_dirs.append(work_dir)
            command = build_command(
                args.openfe_executable,
                transformation,
                output_path,
                work_dir,
                args.resume,
                args.log_config,
            )
            job_name = f"{args.slurm_job_prefix}-{relative_stem}-r{repeat}"
            commands.append((job_name, command))

    detect_duplicates(output_paths, "output")
    detect_duplicates(work_dirs, "work directory")

    for index, (job_name, command) in enumerate(commands):
        if index:
            print()
        if args.format == "commands":
            print(command)
        else:
            print(slurm_script(command, job_name, args.slurm_option))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
