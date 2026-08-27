#!/usr/bin/env python3
"""Safe preflight checks for PaddleHelix compound and drug-discovery inputs.

This helper validates local SMILES files, CSVs, JSON configs, and common app
layout contracts without importing Paddle, starting training, downloading data,
or requiring the original PaddleHelix checkout.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence


SMILES_ALLOWED = re.compile(r"^[A-Za-z0-9@+\-\[\]()=#$:/\\.%*~]+$")
HEADER_TOKENS = {"smiles", "smile", "canonical_smiles", "canonical_smile"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.ok: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"[ERROR] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[WARN] {message}")

    def pass_(self, message: str) -> None:
        self.ok.append(message)
        print(f"[OK] {message}")

    def finish(self) -> int:
        print(
            f"Summary: {len(self.ok)} ok, "
            f"{len(self.warnings)} warning(s), {len(self.errors)} error(s)."
        )
        return 1 if self.errors else 0


def split_csv_arg(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def display(path: Path) -> str:
    return os.fspath(path)


def require_file(path: Path, reporter: Reporter, label: str | None = None) -> bool:
    if path.is_file():
        reporter.pass_(f"found {label or display(path)}")
        return True
    reporter.error(f"missing {label or display(path)}")
    return False


def warn_file(path: Path, reporter: Reporter, label: str | None = None) -> bool:
    if path.is_file():
        reporter.pass_(f"found {label or display(path)}")
        return True
    reporter.warn(f"missing optional/large-run file: {label or display(path)}")
    return False


def require_dir(path: Path, reporter: Reporter, label: str | None = None) -> bool:
    if path.is_dir():
        reporter.pass_(f"found {label or display(path)}")
        return True
    reporter.error(f"missing directory {label or display(path)}")
    return False


def warn_dir(path: Path, reporter: Reporter, label: str | None = None) -> bool:
    if path.is_dir():
        reporter.pass_(f"found {label or display(path)}")
        return True
    reporter.warn(f"missing optional/large-run directory: {label or display(path)}")
    return False


def first_existing(base: Path, candidates: Sequence[str]) -> Path:
    for candidate in candidates:
        path = base / candidate
        if path.exists():
            return path
    return base / candidates[0]


def read_json_config(path: Path, reporter: Reporter) -> object | None:
    if not require_file(path, reporter):
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        reporter.error(f"cannot read JSON config {display(path)}: {exc}")
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        reporter.error(f"JSON parse failed for {display(path)} at line {exc.lineno}: {exc.msg}")
        return None
    reporter.pass_(f"JSON parses: {display(path)}")
    return data


def has_nested_key(data: object, dotted_key: str) -> bool:
    current = data
    for part in dotted_key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False
    return True


def validate_json_configs(paths: Sequence[Path], required_keys: Sequence[str], reporter: Reporter) -> None:
    for path in paths:
        data = read_json_config(path, reporter)
        if data is None:
            continue
        if required_keys:
            missing = [key for key in required_keys if not has_nested_key(data, key)]
            if missing:
                reporter.error(f"{display(path)} missing required JSON key(s): {', '.join(missing)}")
            else:
                reporter.pass_(f"required JSON keys present in {display(path)}")


def load_rdkit(reporter: Reporter):
    try:
        from rdkit import Chem  # type: ignore
    except Exception:
        reporter.warn("RDKit is not installed; using conservative syntax checks only")
        return None
    reporter.pass_("RDKit available for optional SMILES parse checks")
    return Chem


def extract_smiles_token(line: str, suffix: str) -> str:
    stripped = line.strip()
    if suffix.lower() == ".csv" and "," in stripped:
        try:
            row = next(csv.reader([stripped]))
            return row[0].strip() if row else ""
        except csv.Error:
            return stripped.split(",", 1)[0].strip()
    return stripped.split()[0] if stripped.split() else ""


def balanced(text: str, opener: str, closer: str) -> bool:
    depth = 0
    for char in text:
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def validate_smiles_file(path: Path, max_length: int, reporter: Reporter) -> None:
    if not require_file(path, reporter):
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        reporter.error(f"SMILES file is not UTF-8 text: {display(path)}")
        return
    except OSError as exc:
        reporter.error(f"cannot read SMILES file {display(path)}: {exc}")
        return

    chem = load_rdkit(reporter)
    checked = 0
    skipped = 0
    first_data_seen = False
    duplicate_headers: list[int] = []
    bad_lines: list[str] = []
    long_lines: list[int] = []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            skipped += 1
            continue
        token = extract_smiles_token(stripped, path.suffix)
        lower = token.lower()
        if lower in HEADER_TOKENS:
            if first_data_seen:
                duplicate_headers.append(index)
            else:
                skipped += 1
            continue
        first_data_seen = True
        checked += 1
        if max_length and len(token) > max_length:
            long_lines.append(index)
        if not SMILES_ALLOWED.match(token):
            bad_lines.append(f"line {index}: unexpected character(s) in {token!r}")
            continue
        if not balanced(token, "(", ")"):
            bad_lines.append(f"line {index}: unbalanced parentheses in {token!r}")
            continue
        if not balanced(token, "[", "]"):
            bad_lines.append(f"line {index}: unbalanced brackets in {token!r}")
            continue
        if chem is not None and chem.MolFromSmiles(token) is None:
            bad_lines.append(f"line {index}: RDKit could not parse {token!r}")

    if checked == 0:
        reporter.error(f"no SMILES records found in {display(path)}")
    elif bad_lines:
        for detail in bad_lines[:20]:
            reporter.error(f"malformed SMILES in {display(path)}: {detail}")
        if len(bad_lines) > 20:
            reporter.error(f"{len(bad_lines) - 20} additional malformed SMILES line(s) suppressed")
    else:
        reporter.pass_(f"checked {checked} SMILES record(s) in {display(path)}")

    if duplicate_headers:
        reporter.warn(f"possible duplicate SMILES header line(s) in {display(path)}: {duplicate_headers[:10]}")
    if long_lines:
        reporter.warn(
            f"{len(long_lines)} SMILES record(s) exceed --max-smiles-length={max_length}; "
            f"first line(s): {long_lines[:10]}"
        )
    if skipped:
        reporter.pass_(f"skipped {skipped} blank/comment/header line(s) in {display(path)}")


def validate_csv_file(path: Path, required_columns: Sequence[str], reporter: Reporter) -> None:
    if not require_file(path, reporter):
        return
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            rows = []
            for _ in range(6):
                try:
                    rows.append(next(reader))
                except StopIteration:
                    break
    except UnicodeDecodeError:
        reporter.error(f"CSV file is not UTF-8 text: {display(path)}")
        return
    except (OSError, csv.Error) as exc:
        reporter.error(f"cannot parse CSV file {display(path)}: {exc}")
        return

    if not rows:
        reporter.error(f"CSV file is empty: {display(path)}")
        return
    header = [cell.strip() for cell in rows[0]]
    if len(header) < 2:
        reporter.warn(f"CSV {display(path)} has fewer than two columns in the first row")
    else:
        reporter.pass_(f"CSV header read from {display(path)}: {', '.join(header[:8])}")
    if required_columns:
        normalized = {column.lower(): column for column in header}
        missing = [column for column in required_columns if column.lower() not in normalized]
        if missing:
            reporter.error(f"{display(path)} missing required CSV column(s): {', '.join(missing)}")
        else:
            reporter.pass_(f"required CSV columns present in {display(path)}")
    if len(rows) == 1:
        reporter.warn(f"CSV {display(path)} contains a header but no sampled data rows")


def validate_required_files(paths: Sequence[Path], reporter: Reporter) -> None:
    for path in paths:
        require_file(path, reporter)


def check_graphdta(root: Path, reporter: Reporter) -> None:
    dataset_name = root.name.lower()
    require_dir(root / "folds", reporter, "GraphDTA folds/")
    for relative in [
        "folds/train_fold_setting1.txt",
        "folds/test_fold_setting1.txt",
        "ligands_can.txt",
        "proteins.txt",
        "Y",
        f"processed/train/{dataset_name}_train.npz",
        f"processed/test/{dataset_name}_test.npz",
    ]:
        require_file(root / relative, reporter, f"GraphDTA {relative}")
    if dataset_name == "kiba":
        reporter.warn("GraphDTA Kiba training commands usually need --use_kiba_label")


def complete_split_dir(path: Path) -> bool:
    return all((path / name).is_file() for name in ("train.csv", "val.csv", "test.csv"))


def check_moltrans_classification(root: Path, reporter: Reporter) -> None:
    if complete_split_dir(root):
        reporter.pass_(f"MolTrans classification split files found in {display(root)}")
        for split in ("train.csv", "val.csv", "test.csv"):
            validate_csv_file(root / split, [], reporter)
        return

    candidates = [root / name for name in ("full_data", "unseen_drug", "unseen_protein")]
    candidates.extend(path for path in (root / "missing_data").glob("*") if path.is_dir())
    complete = [path for path in candidates if complete_split_dir(path)]
    if complete:
        for path in complete:
            reporter.pass_(f"MolTrans classification split files found in {display(path)}")
        return
    reporter.error(
        "MolTrans classification root must contain train.csv/val.csv/test.csv "
        "or BIOSNAP-style split directories"
    )


def check_text_triplet(root: Path, reporter: Reporter, label: str) -> bool:
    required = ["affinity.txt", "SMILES.txt", "target_seq.txt"]
    found = True
    for name in required:
        found = require_file(root / name, reporter, f"{label} {name}") and found
    return found


def check_moltrans_regression(root: Path, reporter: Reporter) -> None:
    basename = root.name.lower()
    if basename in {"davis", "kiba"}:
        check_text_triplet(root, reporter, f"MolTrans regression {root.name}")
        return
    if basename == "bindingdb":
        for name in [
            "BindingDB_Kd.txt",
            "BindingDB_SMILES.txt",
            "BindingDB_Target_Sequence.txt",
        ]:
            require_file(root / name, reporter, f"MolTrans BindingDB {name}")
        warn_file(root / "BindingDB_SMILES_new.txt", reporter, "MolTrans BindingDB normalized SMILES")
        warn_file(root / "BindingDB_Target_Sequence_new.txt", reporter, "MolTrans BindingDB normalized target sequences")
        return
    if basename == "chembl":
        for name in ["Chem_Affinity.txt", "Chem_SMILES.txt", "ChEMBL_Target_Sequence.txt"]:
            require_file(root / name, reporter, f"MolTrans ChEMBL {name}")
        warn_file(root / "Chem_Kd_nM.txt", reporter, "MolTrans ChEMBL Kd labels")
        return
    if basename == "benchmark":
        require_dir(root / "DAVIStest", reporter, "MolTrans benchmark DAVIStest")
        require_dir(root / "KIBAtest", reporter, "MolTrans benchmark KIBAtest")
        return

    known_children = [root / name for name in ("DAVIS", "KIBA", "BindingDB", "ChEMBL", "benchmark")]
    present = [path for path in known_children if path.exists()]
    if not present:
        reporter.error("MolTrans regression root must be DAVIS, KIBA, BindingDB, ChEMBL, benchmark, or their parent")
        return
    for path in present:
        check_moltrans_regression(path, reporter)


def check_jtvae(root: Path, reporter: Reporter, smiles_supplied: bool) -> None:
    if not smiles_supplied:
        require_file(root / "data/zinc/250k_rndm_zinc_drugs_clean_sorted.smi", reporter, "JT-VAE training SMILES")
    warn_file(root / "data/zinc/vocab.txt", reporter, "JT-VAE vocabulary")
    warn_file(root / "configs/config.json", reporter, "JT-VAE model config")
    warn_dir(root / "zinc_processed", reporter, "JT-VAE processed shards")


def check_sdvae(root: Path, reporter: Reporter, smiles_supplied: bool) -> None:
    require_file(root / "data/data_SD_VAE/context_free_grammars/mol_zinc.grammar", reporter, "SD-VAE grammar")
    require_dir(root / "data/data_SD_VAE/context_free_grammars", reporter, "SD-VAE grammar info folder")
    if not smiles_supplied:
        require_file(root / "data/data_SD_VAE/zinc/250k_rndm_zinc_drugs_clean.smi", reporter, "SD-VAE training SMILES")
    require_file(root / "model_config.json", reporter, "SD-VAE model_config.json")
    warn_dir(root / "model", reporter, "SD-VAE saved model directory")


def check_seqvae(root: Path, reporter: Reporter) -> None:
    require_file(root / "data/zinc_moses/train.csv", reporter, "Seq-VAE train.csv")
    warn_file(root / "data/zinc_moses/test.csv", reporter, "Seq-VAE test.csv")
    require_file(root / "model_config.json", reporter, "Seq-VAE model_config.json")


def check_dtsyn(root: Path, reporter: Reporter) -> None:
    data_root = first_existing(root, ["data", "."])
    for relative in ["ddi.csv", "gene_vector.csv", "rna.csv"]:
        require_file(data_root / relative, reporter, f"DTSyn {relative}")
    warn_file(data_root / "ddi_test.csv", reporter, "DTSyn optional held-out DDI file")


def check_rgcn_synergy(root: Path, reporter: Reporter) -> None:
    data_root = first_existing(root, ["data", "."])
    for relative in [
        "DDI/DDs.csv",
        "DTI/drug_protein_links.tsv",
        "PPI/protein_protein_links.txt",
        "all_drugs_name.fet",
    ]:
        require_file(data_root / relative, reporter, f"RGCN synergy {relative}")


def check_fewshot(root: Path, reporter: Reporter) -> None:
    data_root = first_existing(root, ["data", "."])
    task_dirs = [data_root / name for name in ("muv", "sider", "tox21", "toxcast")]
    present = [path.name for path in task_dirs if path.is_dir()]
    if present:
        reporter.pass_(f"few-shot task directories found: {', '.join(present)}")
    else:
        reporter.error("few-shot data root should contain at least one of muv/, sider/, tox21/, toxcast/")


def inspect_helixdock_dataset_config(path: Path, root: Path, reporter: Reporter) -> None:
    data = read_json_config(path, reporter)
    if not isinstance(data, dict):
        return
    tests = data.get("test")
    if not isinstance(tests, dict):
        reporter.warn(f"HelixDock dataset config {display(path)} has no top-level test object")
        return
    for dataset_name, dataset_cfg in tests.items():
        if not isinstance(dataset_cfg, dict):
            continue
        for key in ("data_dir", "label_file", "complex_id_file", "cache_dir"):
            value = dataset_cfg.get(key)
            if isinstance(value, str) and value:
                raw_path = Path(value)
                if raw_path.is_absolute():
                    resolved = raw_path
                else:
                    resolved = root / raw_path
                if resolved.exists():
                    reporter.pass_(f"HelixDock {dataset_name}.{key} exists")
                else:
                    reporter.warn(f"HelixDock {dataset_name}.{key} points to missing path: {value}")


def check_helixdock(root: Path, reporter: Reporter) -> None:
    warn_file(root / "model/helixdock.pdparams", reporter, "HelixDock model checkpoint")
    for relative in [
        "configs/model_configs/helixdock_encoder.json",
        "configs/model_configs/helixdock_model.json",
        "configs/train_configs/lr8e-4_ema.json",
    ]:
        read_json_config(root / relative, reporter)
    for relative in [
        "configs/dataset_configs/pdbbind_core.json",
        "configs/dataset_configs/poesbusters.json",
    ]:
        inspect_helixdock_dataset_config(root / relative, root, reporter)
    warn_dir(root / "data/processed/pdbbind_core_processed", reporter, "HelixDock processed PDBbind core data")
    warn_dir(root / "data/processed/posebuster_processed", reporter, "HelixDock processed PoseBusters data")
    reporter.warn("HelixDock reproduction is heavy and may require Paddle, RDKit 2022.3.3, OpenBabel, GPUs, and non-commercial/license approval")


def check_dataset_layout(kind: str, root: Path, smiles_supplied: bool, reporter: Reporter) -> None:
    if not root.exists():
        reporter.error(f"dataset root does not exist: {display(root)}")
        return
    if kind == "graphdta":
        check_graphdta(root, reporter)
    elif kind == "moltrans-classification":
        check_moltrans_classification(root, reporter)
    elif kind == "moltrans-regression":
        check_moltrans_regression(root, reporter)
    elif kind == "jtvae":
        check_jtvae(root, reporter, smiles_supplied)
    elif kind == "sdvae":
        check_sdvae(root, reporter, smiles_supplied)
    elif kind == "seqvae":
        check_seqvae(root, reporter)
    elif kind == "dtsyn":
        check_dtsyn(root, reporter)
    elif kind == "rgcn-synergy":
        check_rgcn_synergy(root, reporter)
    elif kind == "fewshot":
        check_fewshot(root, reporter)
    elif kind == "helixdock":
        check_helixdock(root, reporter)
    else:
        reporter.error(f"unknown dataset kind: {kind}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate local PaddleHelix compound/drug-discovery SMILES, CSV, "
            "JSON config, and dataset layout inputs without importing Paddle or downloading data."
        )
    )
    parser.add_argument("--smiles-file", action="append", default=[], type=Path, help="SMILES or CSV file to validate; may be repeated")
    parser.add_argument("--max-smiles-length", type=int, default=0, help="warn when a SMILES token exceeds this length")
    parser.add_argument("--csv-file", action="append", default=[], type=Path, help="CSV file to parse and optionally check columns; may be repeated")
    parser.add_argument("--require-columns", default="", help="comma-separated CSV columns required in each --csv-file")
    parser.add_argument("--json-config", action="append", default=[], type=Path, help="JSON config to parse; may be repeated")
    parser.add_argument("--require-json-keys", default="", help="comma-separated required JSON keys; dot notation supports nested keys")
    parser.add_argument("--require-files", default="", help="comma-separated files that must exist, relative to the current directory unless absolute")
    parser.add_argument(
        "--dataset-kind",
        choices=[
            "graphdta",
            "moltrans-classification",
            "moltrans-regression",
            "jtvae",
            "sdvae",
            "seqvae",
            "dtsyn",
            "rgcn-synergy",
            "fewshot",
            "helixdock",
        ],
        help="common PaddleHelix compound app layout to check",
    )
    parser.add_argument("--dataset-root", type=Path, help="root directory for --dataset-kind checks")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()

    required_columns = split_csv_arg(args.require_columns)
    required_json_keys = split_csv_arg(args.require_json_keys)
    required_files = [Path(item) for item in split_csv_arg(args.require_files)]

    if not any([args.smiles_file, args.csv_file, args.json_config, args.dataset_kind, required_files]):
        parser.error("provide at least one --smiles-file, --csv-file, --json-config, --dataset-kind, or --require-files")

    for path in args.smiles_file:
        validate_smiles_file(path, args.max_smiles_length, reporter)
    for path in args.csv_file:
        validate_csv_file(path, required_columns, reporter)
    validate_json_configs(args.json_config, required_json_keys, reporter)
    validate_required_files(required_files, reporter)

    if args.dataset_kind:
        if args.dataset_root is None:
            reporter.error("--dataset-root is required with --dataset-kind")
        else:
            check_dataset_layout(args.dataset_kind, args.dataset_root, bool(args.smiles_file), reporter)

    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
