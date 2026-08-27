#!/usr/bin/env python3
"""Safely check AlphaFold 3 runtime prerequisites without running predictions."""

from __future__ import annotations

import argparse
import importlib
import importlib.resources
import os
from pathlib import Path
import shutil
import sys
from typing import Iterable

HMMER_BINARIES = ("jackhmmer", "nhmmer", "hmmalign", "hmmsearch", "hmmbuild")
CCD_RESOURCES = (
    "constants/converters/ccd.pickle",
    "constants/converters/chemical_component_sets.pickle",
)
DEFAULT_DATABASE_FILES = {
    "small_bfd": "bfd-first_non_consensus_sequences.fasta",
    "mgnify": "mgy_clusters_2022_05.fa",
    "uniprot_cluster_annot": "uniprot_all_2021_04.fa",
    "uniref90": "uniref90_2022_05.fa",
    "ntrna": "nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta",
    "rfam": "rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta",
    "rna_central": "rnacentral_active_seq_id_90_cov_80_linclust.fasta",
    "pdb": "mmcif_files",
    "seqres": "pdb_seqres_2022_09_28.fasta",
}
Z_VALUE_FLAGS = {
    "small_bfd": "small_bfd_z_value",
    "mgnify": "mgnify_z_value",
    "uniprot_cluster_annot": "uniprot_cluster_annot_z_value",
    "uniref90": "uniref90_z_value",
    "ntrna": "ntrna_z_value",
    "rfam": "rfam_z_value",
    "rna_central": "rna_central_z_value",
}


class Reporter:
    def __init__(self) -> None:
        self.errors = 0
        self.warnings = 0

    def ok(self, message: str) -> None:
        print(f"OK: {message}")

    def warn(self, message: str) -> None:
        self.warnings += 1
        print(f"WARN: {message}")

    def fail(self, message: str) -> None:
        self.errors += 1
        print(f"FAIL: {message}")


def is_sharded_spec(path: str) -> bool:
    name = Path(path).name
    if "@" not in name:
        return False
    prefix, shard_count = name.rsplit("@", 1)
    return bool(prefix) and shard_count.isdigit()


def expand_db_path(path: str, db_dirs: Iterable[Path]) -> list[Path]:
    if "${DB_DIR}" not in path:
        return [Path(path)]
    return [Path(path.replace("${DB_DIR}", str(db_dir))) for db_dir in db_dirs]


def check_imports(reporter: Reporter) -> None:
    modules = [
        "alphafold3",
        "alphafold3.common.folding_input",
        "alphafold3.data.pipeline",
        "alphafold3.model.model_config",
        "alphafold3.structure",
    ]
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure.
            reporter.fail(f"import {module_name!r} failed: {exc}")
        else:
            reporter.ok(f"import {module_name!r}")


def check_ccd_resources(reporter: Reporter) -> None:
    try:
        import alphafold3  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        reporter.fail(f"cannot inspect CCD resources because alphafold3 import failed: {exc}")
        return

    package_root = importlib.resources.files(alphafold3)
    for resource in CCD_RESOURCES:
        try:
            target = package_root.joinpath(*resource.split("/"))
            if target.is_file():
                reporter.ok(f"generated CCD resource present: {resource}")
            else:
                reporter.warn(f"generated CCD resource missing: {resource}; run the package data-build step if ligand/CCD code fails")
        except Exception as exc:  # noqa: BLE001
            reporter.warn(f"could not inspect CCD resource {resource}: {exc}")


def check_hmmer(reporter: Reporter) -> None:
    for binary in HMMER_BINARIES:
        path = shutil.which(binary)
        if path:
            reporter.ok(f"{binary} found at {path}")
        else:
            reporter.fail(f"{binary} not found on PATH")


def check_optional_path(reporter: Reporter, label: str, value: str | None, *, expect_dir: bool = True) -> None:
    if not value:
        reporter.warn(f"{label} not supplied; skipping path check")
        return
    path = Path(value)
    if not path.exists():
        reporter.fail(f"{label} does not exist: {value}")
        return
    if expect_dir and not path.is_dir():
        reporter.fail(f"{label} exists but is not a directory: {value}")
        return
    if not os.access(path, os.R_OK):
        reporter.fail(f"{label} is not readable: {value}")
        return
    reporter.ok(f"{label} exists and is readable: {value}")


def check_default_databases(reporter: Reporter, db_dirs: list[Path]) -> None:
    if not db_dirs:
        reporter.warn("no --db_dir supplied; skipping default database layout checks")
        return
    for db_dir in db_dirs:
        if not db_dir.exists():
            reporter.fail(f"database root does not exist: {db_dir}")
            continue
        if not db_dir.is_dir():
            reporter.fail(f"database root is not a directory: {db_dir}")
            continue
        if not os.access(db_dir, os.R_OK | os.X_OK):
            reporter.fail(f"database root lacks read/execute permissions: {db_dir}")
            continue
        reporter.ok(f"database root is readable: {db_dir}")

    for label, relative in DEFAULT_DATABASE_FILES.items():
        candidates = [db_dir / relative for db_dir in db_dirs]
        if any(candidate.exists() for candidate in candidates):
            reporter.ok(f"default database entry found for {label}: {relative}")
        else:
            reporter.warn(f"default database entry not found for {label}: {relative}")


def check_explicit_database_paths(reporter: Reporter, args: argparse.Namespace, db_dirs: list[Path]) -> None:
    for label in DEFAULT_DATABASE_FILES:
        arg_name = f"{label}_database_path"
        value = getattr(args, arg_name, None)
        if not value:
            continue
        z_flag = Z_VALUE_FLAGS.get(label)
        z_value = getattr(args, z_flag, None) if z_flag else None
        if is_sharded_spec(value):
            if z_flag and z_value is None:
                reporter.warn(f"{arg_name} uses sharded spec {value!r} but --{z_flag} was not supplied")
            else:
                reporter.ok(f"{arg_name} uses sharded spec with matching Z-value flag")
            continue
        candidates = expand_db_path(value, db_dirs)
        if any(candidate.exists() for candidate in candidates):
            reporter.ok(f"{arg_name} path exists: {value}")
        else:
            reporter.fail(f"{arg_name} path not found: {value}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_dir", help="Optional model parameter directory to check.")
    parser.add_argument("--db_dir", action="append", default=[], help="Database root to check. Repeatable.")
    parser.add_argument("--skip_imports", action="store_true", help="Skip AlphaFold 3 import checks.")
    parser.add_argument("--skip_ccd", action="store_true", help="Skip generated CCD resource checks.")
    parser.add_argument("--skip_hmmer", action="store_true", help="Skip HMMER binary checks.")
    parser.add_argument("--skip_default_databases", action="store_true", help="Skip default database layout checks.")

    for label in DEFAULT_DATABASE_FILES:
        parser.add_argument(f"--{label}_database_path", help=f"Explicit path for {label} database.")
    for flag in Z_VALUE_FLAGS.values():
        parser.add_argument(f"--{flag}", help=f"Z-value paired with sharded database flag {flag}.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    reporter = Reporter()
    db_dirs = [Path(item) for item in args.db_dir]

    if not args.skip_imports:
        check_imports(reporter)
    if not args.skip_ccd:
        check_ccd_resources(reporter)
    if not args.skip_hmmer:
        check_hmmer(reporter)

    check_optional_path(reporter, "model_dir", args.model_dir)
    if not args.skip_default_databases:
        check_default_databases(reporter, db_dirs)
    check_explicit_database_paths(reporter, args, db_dirs)

    print(f"Summary: {reporter.errors} error(s), {reporter.warnings} warning(s)")
    return 2 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
