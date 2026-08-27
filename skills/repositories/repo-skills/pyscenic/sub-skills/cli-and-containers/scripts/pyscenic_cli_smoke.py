#!/usr/bin/env python3
"""Safe pySCENIC CLI smoke checks and command-template writer.

The default mode only prints help for this helper. Use --check-help to run
installed CLI help commands. Use --emit-template or --write-args-dir to produce
command templates. No pySCENIC pipeline step, container command, download, or
training job is executed by this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

HELP_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("pyscenic", "--help"),
    ("pyscenic", "grn", "--help"),
    ("pyscenic", "add_cor", "--help"),
    ("pyscenic", "ctx", "--help"),
    ("pyscenic", "aucell", "--help"),
    ("arboreto_with_multiprocessing.py", "--help"),
)

IMPORT_MODULES: tuple[str, ...] = (
    "pyscenic",
    "pyscenic.cli.pyscenic",
    "pyscenic.aucell",
    "pyscenic.prune",
    "pyscenic.utils",
)


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def shell_join(command: Sequence[str]) -> str:
    return " ".join(quote_for_shell(part) for part in command)


def quote_for_shell(value: str) -> str:
    if not value:
        return "''"
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@%+=:,./-")
    if all(char in safe for char in value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def run_command(command: Sequence[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            list(command),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return 124, stdout, stderr or "command timed out after 30 seconds"
    return result.returncode, result.stdout, result.stderr


def check_imports() -> int:
    failures = 0
    for module in IMPORT_MODULES:
        code = f"import {module}; print('ok')"
        returncode, stdout, stderr = run_command((sys.executable, "-c", code))
        if returncode == 0:
            print(f"[import:ok] {module}")
        else:
            failures += 1
            print(f"[import:fail] {module} exited {returncode}", file=sys.stderr)
            if stderr.strip():
                print(stderr.strip(), file=sys.stderr)
            elif stdout.strip():
                print(stdout.strip(), file=sys.stderr)
    return failures


def check_help() -> int:
    failures = 0
    for command in HELP_COMMANDS:
        executable = command[0]
        if shutil.which(executable) is None:
            failures += 1
            print(f"[help:fail] {executable} not found on PATH", file=sys.stderr)
            continue
        returncode, stdout, stderr = run_command(command)
        if returncode == 0:
            first_line = stdout.splitlines()[0] if stdout.splitlines() else "help returned no stdout"
            print(f"[help:ok] {shell_join(command)} :: {first_line}")
        else:
            failures += 1
            print(f"[help:fail] {shell_join(command)} exited {returncode}", file=sys.stderr)
            if stderr.strip():
                print(stderr.strip(), file=sys.stderr)
            elif stdout.strip():
                print(stdout.strip(), file=sys.stderr)
    return failures


def path_join(root: str, *parts: str) -> str:
    return "/".join([root.rstrip("/"), *[part.strip("/") for part in parts]])


def command_templates(workdir: str, workers: int, seed: int, transpose: bool) -> dict[str, list[str]]:
    expr = path_join(workdir, "expression_cells_by_genes.csv")
    if transpose:
        expr = path_join(workdir, "expression_genes_by_cells.tsv")
    tfs = path_join(workdir, "tfs.txt")
    out = path_join(workdir, "out")
    db1 = path_join(workdir, "databases", "db1.genes_vs_motifs.rankings.feather")
    db2 = path_join(workdir, "databases", "db2.genes_vs_motifs.rankings.feather")
    annotations = path_join(workdir, "motif_annotations.tbl")
    transpose_flag = ["--transpose"] if transpose else []
    return {
        "grn": [
            "pyscenic",
            "grn",
            *transpose_flag,
            "--method",
            "grnboost2",
            "--num_workers",
            str(workers),
            "--seed",
            str(seed),
            "-o",
            path_join(out, "adjacencies.tsv"),
            expr,
            tfs,
        ],
        "add_cor": [
            "pyscenic",
            "add_cor",
            *transpose_flag,
            "--mask_dropouts",
            "-o",
            path_join(out, "adjacencies_with_rho.tsv"),
            path_join(out, "adjacencies.tsv"),
            expr,
        ],
        "ctx": [
            "pyscenic",
            "ctx",
            *transpose_flag,
            path_join(out, "adjacencies.tsv"),
            db1,
            db2,
            "--annotations_fname",
            annotations,
            "--expression_mtx_fname",
            expr,
            "--mode",
            "custom_multiprocessing",
            "--num_workers",
            str(workers),
            "--output",
            path_join(out, "regulons.csv"),
        ],
        "aucell": [
            "pyscenic",
            "aucell",
            *transpose_flag,
            expr,
            path_join(out, "regulons.csv"),
            "--num_workers",
            str(workers),
            "--seed",
            str(seed),
            "-o",
            path_join(out, "auc_mtx.csv"),
        ],
        "arboreto_multiprocessing": [
            "arboreto_with_multiprocessing.py",
            *transpose_flag,
            "--method",
            "grnboost2",
            "--num_workers",
            str(workers),
            "--seed",
            str(seed),
            "--output",
            path_join(out, "adjacencies.tsv"),
            expr,
            tfs,
        ],
    }


def print_templates(templates: dict[str, list[str]]) -> None:
    print("# pySCENIC command templates; inspect paths/resources before running.")
    for name, command in templates.items():
        print(f"\n## {name}")
        print(shell_join(command))


def write_args_files(directory: Path, templates: dict[str, list[str]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("grn", "add_cor", "ctx", "aucell"):
        command = templates[name]
        args = command[1:]
        path = directory / f"{name}.args.txt"
        path.write_text("\n".join(args) + "\n", encoding="utf-8")
        print(f"[write] {path}")
    manifest = {
        "note": "Invoke with pyscenic @file.args.txt after editing paths/resources. Args files use one argument per line and do not include shell quotes.",
        "files": [f"{name}.args.txt" for name in ("grn", "add_cor", "ctx", "aucell")],
    }
    (directory / "README.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[write] {directory / 'README.json'}")


def make_fixtures(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    expr_path = directory / "expression_cells_by_genes.csv"
    tfs_path = directory / "tfs.txt"
    with expr_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cell", "TF1", "TF2", "GeneA", "GeneB"])
        writer.writerow(["Cell1", "1", "0", "3", "4"])
        writer.writerow(["Cell2", "2", "1", "0", "5"])
        writer.writerow(["Cell3", "0", "3", "2", "1"])
        writer.writerow(["Cell4", "4", "2", "1", "0"])
    tfs_path.write_text("TF1\nTF2\n", encoding="utf-8")
    (directory / "out").mkdir(exist_ok=True)
    print(f"[write] {expr_path}")
    print(f"[write] {tfs_path}")
    print(f"[write] {directory / 'out'}")
    print("Tiny fixtures are for path/orientation planning only; they are not a biological test dataset.")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely check pySCENIC CLI help and generate dry-run command templates.",
    )
    parser.add_argument(
        "--check-help",
        action="store_true",
        help="Run installed pySCENIC and arboreto_with_multiprocessing.py help commands.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check core pySCENIC imports using the current Python interpreter.",
    )
    parser.add_argument(
        "--emit-template",
        action="store_true",
        help="Print local CLI command templates without executing pySCENIC pipeline steps.",
    )
    parser.add_argument(
        "--write-args-dir",
        type=Path,
        help="Write editable pyscenic @args.txt templates into this directory.",
    )
    parser.add_argument(
        "--make-fixtures",
        type=Path,
        help="Create tiny expression and TF-list fixtures for path/orientation planning.",
    )
    parser.add_argument(
        "--workdir",
        default="/data",
        help="Runtime project root to use in generated templates. Default: /data.",
    )
    parser.add_argument(
        "--workers",
        type=positive_int,
        default=4,
        help="Worker count to place in generated templates. Default: 4.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=777,
        help="Seed to place in generated templates. Default: 777.",
    )
    parser.add_argument(
        "--transpose",
        action="store_true",
        help="Generate templates for genes-by-cells text expression input.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    failures = 0

    if args.check_imports:
        failures += check_imports()
    if args.check_help:
        failures += check_help()

    templates = command_templates(args.workdir, args.workers, args.seed, args.transpose)
    if args.emit_template:
        print_templates(templates)
    if args.write_args_dir:
        write_args_files(args.write_args_dir, templates)
    if args.make_fixtures:
        make_fixtures(args.make_fixtures)

    if not any((args.check_imports, args.check_help, args.emit_template, args.write_args_dir, args.make_fixtures)):
        print("No action requested. Use --help for options.")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
