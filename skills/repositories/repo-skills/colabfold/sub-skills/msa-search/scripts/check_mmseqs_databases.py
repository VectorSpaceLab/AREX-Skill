#!/usr/bin/env python3
"""Read-only checks for ColabFold MMseqs2 database layouts."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseSpec:
    label: str
    basename: str
    required: bool


def marker_exists(db_dir: Path, basename: str, suffixes: tuple[str, ...]) -> bool:
    return any((db_dir / f"{basename}{suffix}").exists() for suffix in suffixes)


def check_mmseqs(binary: str) -> tuple[str, bool]:
    path = shutil.which(binary) if os.sep not in binary else binary
    if not path or not Path(path).exists():
        return f"FAIL mmseqs binary not found: {binary}", False

    try:
        result = subprocess.run(
            [path, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"FAIL could not execute {path!r}: {exc}", False

    output = result.stdout or ""
    gpu_hint = "gpuserver" in output or "--gpu" in output
    status = "OK" if result.returncode == 0 else "WARN"
    return f"{status} mmseqs executable: {path} (gpu help detected: {gpu_hint})", result.returncode == 0


def build_specs(args: argparse.Namespace) -> list[DatabaseSpec]:
    return [
        DatabaseSpec("UniRef", args.db1, True),
        DatabaseSpec("Environmental", args.db3, bool(args.use_env)),
        DatabaseSpec("Template", args.db2, bool(args.use_templates)),
        DatabaseSpec("Environmental pairing", args.db4, bool(args.use_env_pairing)),
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a ColabFold MMseqs2 database directory without downloading, "
            "indexing, deleting, or modifying files."
        )
    )
    parser.add_argument("db_dir", type=Path, help="Directory containing MMseqs2 database basenames")
    parser.add_argument("--db1", default="uniref30_2302_db", help="UniRef database basename")
    parser.add_argument("--db2", default="pdb100_230517", help="Template database basename")
    parser.add_argument("--db3", default="colabfold_envdb_202108_db", help="Environmental database basename")
    parser.add_argument("--db4", default="spire_ctg10_2401_db", help="Environmental pairing database basename")
    parser.add_argument("--use-env", action=argparse.BooleanOptionalAction, default=True, help="Require/check environmental DB")
    parser.add_argument("--use-templates", action="store_true", help="Require/check template DB")
    parser.add_argument("--use-env-pairing", action="store_true", help="Require/check environmental pairing DB")
    parser.add_argument("--require-index", action="store_true", help="Fail when required databases lack .idx/.idx.index markers")
    parser.add_argument("--mode", choices=("cpu", "gpu", "server"), default="cpu", help="Operational mode for advisory messages")
    parser.add_argument("--mmseqs", default="mmseqs", help="MMseqs2 binary name or path for --check-mmseqs")
    parser.add_argument("--check-mmseqs", action="store_true", help="Also run a safe mmseqs --help availability check")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    db_dir = args.db_dir.expanduser().resolve()
    problems: list[str] = []
    warnings: list[str] = []

    print(f"Database directory: {db_dir}")
    if not db_dir.exists():
        print("FAIL database directory does not exist")
        return 2
    if not db_dir.is_dir():
        print("FAIL database path is not a directory")
        return 2

    if args.check_mmseqs:
        message, ok = check_mmseqs(args.mmseqs)
        print(message)
        if not ok:
            problems.append("mmseqs availability check failed")

    if os.environ.get("MMSEQS_IGNORE_INDEX"):
        warnings.append("MMSEQS_IGNORE_INDEX is set; ColabFold search will ignore indexes even if present")

    if args.mode in {"gpu", "server"} and "CUDA_VISIBLE_DEVICES" not in os.environ:
        warnings.append("CUDA_VISIBLE_DEVICES is not set; GPU device selection will use the process default")

    if args.mode in {"gpu", "server"} and not args.require_index:
        warnings.append("GPU/server mode usually benefits from indexes; consider rerunning with --require-index")

    dbtype_suffixes = (".dbtype",)
    index_suffixes = (".idx", ".idx.index")

    for spec in build_specs(args):
        dbtype_ok = marker_exists(db_dir, spec.basename, dbtype_suffixes)
        index_ok = marker_exists(db_dir, spec.basename, index_suffixes)
        requirement = "required" if spec.required else "optional"
        print(f"{spec.label}: {spec.basename} ({requirement})")
        print(f"  dbtype: {'OK' if dbtype_ok else 'MISSING'}")
        print(f"  index:  {'OK' if index_ok else 'MISSING'}")

        if spec.required and not dbtype_ok:
            problems.append(f"missing required database marker: {spec.basename}.dbtype")
        if spec.required and args.require_index and not index_ok:
            problems.append(f"missing required index marker for: {spec.basename}")
        if spec.required and not index_ok and not args.require_index:
            warnings.append(f"{spec.basename} has no index marker; batch CPU search may still work, server/gpu may not")

    ready_markers = [
        "DOWNLOADS_READY",
        "UNIREF30_READY",
        "COLABDB_READY",
        "PDB_READY",
        "PDB100_READY",
        "PDB_MMCIF_READY",
    ]
    present_ready = [marker for marker in ready_markers if (db_dir / marker).exists()]
    if present_ready:
        print("Ready markers: " + ", ".join(present_ready))
    else:
        warnings.append("no setup ready-marker files found; this is acceptable for custom layouts but worth confirming")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  WARN {warning}")

    if problems:
        print("Problems:")
        for problem in problems:
            print(f"  FAIL {problem}")
        return 1

    print("OK database layout checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
