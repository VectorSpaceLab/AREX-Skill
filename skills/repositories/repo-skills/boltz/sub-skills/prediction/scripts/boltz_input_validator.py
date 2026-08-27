#!/usr/bin/env python3
"""Lightweight Boltz prediction input validator.

This script is intentionally conservative and download-free. It does not import
Boltz, RDKit, PyTorch, or model checkpoints. It validates common YAML, FASTA,
A3M, CSV, cache, MSA, auth, and output-shape issues before `boltz predict`.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Any

VALID_INPUT_SUFFIXES = {".yaml", ".yml", ".fasta", ".fa", ".fas"}
PROTEIN_ALPHABET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ-.*")


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def print(self) -> None:
        for label, messages in (
            ("ERROR", self.errors),
            ("WARNING", self.warnings),
            ("NOTE", self.notes),
        ):
            for message in messages:
                print(f"{label}: {message}")
        if not self.errors and not self.warnings:
            print("OK: no blocking issues or warnings found.")
        elif not self.errors:
            print("OK: no blocking issues found; review warnings before running Boltz.")


def load_yaml(path: Path, reporter: Reporter) -> Any | None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        reporter.error(
            "PyYAML is required for YAML validation. Install with `pip install pyyaml` "
            "or validate only FASTA/A3M/CSV inputs."
        )
        return None

    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"Could not parse YAML {path}: {exc}")
        return None


def input_files(data: Path, reporter: Reporter) -> list[Path]:
    if data.is_dir():
        files = sorted(data.iterdir())
        if not files:
            reporter.error(f"Input directory is empty: {data}")
            return []
        selected: list[Path] = []
        for child in files:
            if child.is_dir():
                reporter.error(
                    f"Input directory contains nested directory {child.name}; "
                    "Boltz expects only YAML/FASTA files as direct children."
                )
                continue
            if child.suffix.lower() not in VALID_INPUT_SUFFIXES:
                reporter.error(
                    f"Input directory contains unsupported file {child.name}; "
                    "move MSA/template/output files elsewhere."
                )
                continue
            selected.append(child)
        return selected
    if not data.exists():
        reporter.error(f"Input path does not exist: {data}")
        return []
    if data.suffix.lower() not in VALID_INPUT_SUFFIXES:
        reporter.error(
            f"Unsupported input suffix {data.suffix!r}; expected YAML or FASTA."
        )
        return []
    return [data]


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def resolve_support_path(raw_path: str, input_path: Path) -> Path:
    support = Path(raw_path).expanduser()
    if support.is_absolute():
        return support
    candidate = input_path.parent / support
    if candidate.exists():
        return candidate
    return Path.cwd() / support


def classify_msa(msa: Any) -> str:
    if msa is None or msa == "":
        return "auto"
    if msa == 0:
        return "auto"
    if isinstance(msa, str) and msa.lower() == "empty":
        return "empty"
    return "custom"


def validate_yaml(path: Path, args: argparse.Namespace, reporter: Reporter) -> None:
    data = load_yaml(path, reporter)
    if data is None:
        return
    if not isinstance(data, dict):
        reporter.error(f"{path.name}: YAML root must be a mapping.")
        return

    version = data.get("version", 1)
    if version != 1:
        reporter.error(f"{path.name}: version must be 1, got {version!r}.")

    sequences = data.get("sequences")
    if not isinstance(sequences, list) or not sequences:
        reporter.error(f"{path.name}: `sequences` must be a non-empty list.")
        sequences = []

    chain_ids: set[str] = set()
    ligand_ids: set[str] = set()
    multi_copy_ligands: set[str] = set()
    msa_modes: set[str] = set()
    protein_count = 0

    for index, item in enumerate(sequences, start=1):
        if not isinstance(item, dict) or len(item) != 1:
            reporter.error(
                f"{path.name}: sequence entry {index} must contain exactly one entity key."
            )
            continue
        entity_type, spec = next(iter(item.items()))
        if entity_type not in {"protein", "dna", "rna", "ligand"}:
            reporter.error(
                f"{path.name}: invalid entity type {entity_type!r} at sequence {index}."
            )
            continue
        if not isinstance(spec, dict):
            reporter.error(f"{path.name}: {entity_type} entry {index} must be a mapping.")
            continue

        ids = spec.get("id")
        if ids is None:
            reporter.error(f"{path.name}: {entity_type} entry {index} is missing `id`.")
            ids_list: list[Any] = []
        else:
            ids_list = as_list(ids)
        normalized_ids: list[str] = []
        for chain_id in ids_list:
            if not isinstance(chain_id, str) or not chain_id:
                reporter.error(
                    f"{path.name}: {entity_type} entry {index} has invalid chain id {chain_id!r}."
                )
                continue
            if chain_id in chain_ids:
                reporter.error(f"{path.name}: duplicate chain id {chain_id!r}.")
            chain_ids.add(chain_id)
            normalized_ids.append(chain_id)

        if entity_type in {"protein", "dna", "rna"}:
            sequence = spec.get("sequence")
            if not isinstance(sequence, str) or not sequence.strip():
                reporter.error(
                    f"{path.name}: {entity_type} {normalized_ids or index} needs a non-empty sequence."
                )
            modifications = spec.get("modifications", [])
            if modifications not in (None, []) and not isinstance(modifications, list):
                reporter.warn(
                    f"{path.name}: modifications for {normalized_ids or index} should be a list."
                )
            if entity_type == "protein":
                protein_count += len(normalized_ids) or 1
                msa = spec.get("msa", None)
                mode = classify_msa(msa)
                msa_modes.add(mode)
                if mode == "custom" and isinstance(msa, str):
                    validate_msa_path(msa, path, reporter)
        elif entity_type == "ligand":
            smiles = spec.get("smiles")
            ccd = spec.get("ccd")
            if bool(smiles) == bool(ccd):
                reporter.error(
                    f"{path.name}: ligand {normalized_ids or index} must set exactly one of `smiles` or `ccd`."
                )
            for chain_id in normalized_ids:
                ligand_ids.add(chain_id)
            if len(normalized_ids) > 1:
                multi_copy_ligands.update(normalized_ids)

    if protein_count and "custom" in msa_modes and "auto" in msa_modes:
        reporter.error(
            f"{path.name}: mixes custom protein MSA paths with omitted/auto MSA fields; "
            "provide all MSAs, set `msa: empty`, or use MSA server consistently."
        )
    if protein_count and "auto" in msa_modes and not args.use_msa_server:
        reporter.error(
            f"{path.name}: has protein chains without custom MSA; pass --use_msa_server "
            "to Boltz or add `msa` paths/`msa: empty`."
        )
    if protein_count and "empty" in msa_modes:
        reporter.warn(
            f"{path.name}: uses `msa: empty`; this is single-sequence mode and may reduce accuracy."
        )

    validate_constraints(path, data.get("constraints", []), chain_ids, reporter)
    validate_templates(path, data.get("templates", []), reporter)
    validate_properties(path, data.get("properties", []), ligand_ids, multi_copy_ligands, reporter)


def validate_msa_path(raw_path: str, input_path: Path, reporter: Reporter) -> None:
    if raw_path.lower() == "empty":
        return
    support_path = resolve_support_path(raw_path, input_path)
    suffixes = [suffix.lower() for suffix in support_path.suffixes]
    if not suffixes:
        reporter.warn(f"MSA path {raw_path!r} has no suffix; expected .a3m or .csv.")
    elif suffixes[-1] == ".gz" and len(suffixes) >= 2 and suffixes[-2] == ".a3m":
        pass
    elif suffixes[-1] not in {".a3m", ".csv"}:
        reporter.warn(f"MSA path {raw_path!r} should usually be .a3m, .a3m.gz, or .csv.")
    if support_path.exists():
        if support_path.suffix.lower() == ".csv":
            validate_csv(support_path, reporter, nested=True)
        elif ".a3m" in suffixes:
            validate_a3m(support_path, reporter, nested=True)
    else:
        reporter.warn(
            f"MSA path {raw_path!r} was not found relative to the input file or current directory."
        )


def validate_constraints(path: Path, constraints: Any, chain_ids: set[str], reporter: Reporter) -> None:
    if constraints in (None, []):
        return
    if not isinstance(constraints, list):
        reporter.error(f"{path.name}: `constraints` must be a list.")
        return
    for index, constraint in enumerate(constraints, start=1):
        if not isinstance(constraint, dict) or len(constraint) != 1:
            reporter.error(f"{path.name}: constraint {index} must have one type key.")
            continue
        kind, spec = next(iter(constraint.items()))
        if kind not in {"bond", "pocket", "contact"}:
            reporter.error(f"{path.name}: invalid constraint type {kind!r}.")
            continue
        if not isinstance(spec, dict):
            reporter.error(f"{path.name}: constraint {index} spec must be a mapping.")
            continue
        if kind == "bond":
            for key in ("atom1", "atom2"):
                atom = spec.get(key)
                if not isinstance(atom, list) or len(atom) != 3:
                    reporter.error(f"{path.name}: bond {key} must be [chain, residue, atom].")
                elif atom[0] not in chain_ids:
                    reporter.warn(f"{path.name}: bond {key} references unknown chain {atom[0]!r}.")
        elif kind == "pocket":
            if spec.get("binder") not in chain_ids:
                reporter.warn(f"{path.name}: pocket binder references unknown chain {spec.get('binder')!r}.")
            contacts = spec.get("contacts")
            if not isinstance(contacts, list) or not contacts:
                reporter.error(f"{path.name}: pocket contacts must be a non-empty list.")
            check_distance(path, kind, spec.get("max_distance", 6.0), reporter)
            if spec.get("force") is True:
                reporter.note(f"{path.name}: forced pocket constraint should be paired with intentional potential steering.")
        elif kind == "contact":
            for key in ("token1", "token2"):
                token = spec.get(key)
                if not isinstance(token, list) or len(token) != 2:
                    reporter.error(f"{path.name}: contact {key} must be [chain, residue_or_atom].")
                elif token[0] not in chain_ids:
                    reporter.warn(f"{path.name}: contact {key} references unknown chain {token[0]!r}.")
            check_distance(path, kind, spec.get("max_distance", 6.0), reporter)
            if spec.get("force") is True:
                reporter.note(f"{path.name}: forced contact constraint should be paired with intentional potential steering.")


def check_distance(path: Path, kind: str, value: Any, reporter: Reporter) -> None:
    try:
        distance = float(value)
    except (TypeError, ValueError):
        reporter.error(f"{path.name}: {kind} max_distance must be numeric.")
        return
    if not 4.0 <= distance <= 20.0:
        reporter.warn(f"{path.name}: {kind} max_distance {distance:g} is outside the documented 4-20 Å range.")


def validate_templates(path: Path, templates: Any, reporter: Reporter) -> None:
    if templates in (None, []):
        return
    if not isinstance(templates, list):
        reporter.error(f"{path.name}: `templates` must be a list.")
        return
    for index, template in enumerate(templates, start=1):
        if not isinstance(template, dict):
            reporter.error(f"{path.name}: template {index} must be a mapping.")
            continue
        raw_template_path = template.get("cif") or template.get("pdb") or template.get("path")
        if not raw_template_path:
            reporter.error(f"{path.name}: template {index} must provide `cif` or `pdb`.")
        elif isinstance(raw_template_path, str):
            resolved = resolve_support_path(raw_template_path, path)
            if not resolved.exists():
                reporter.warn(f"{path.name}: template file {raw_template_path!r} was not found.")
        if template.get("force") is True and "threshold" not in template:
            reporter.error(f"{path.name}: template {index} has force: true but no threshold.")


def validate_properties(
    path: Path,
    properties: Any,
    ligand_ids: set[str],
    multi_copy_ligands: set[str],
    reporter: Reporter,
) -> None:
    if properties in (None, []):
        return
    if not isinstance(properties, list):
        reporter.error(f"{path.name}: `properties` must be a list.")
        return
    affinity_binders: list[str] = []
    for index, prop in enumerate(properties, start=1):
        if not isinstance(prop, dict) or len(prop) != 1:
            reporter.error(f"{path.name}: property {index} must have one type key.")
            continue
        kind, spec = next(iter(prop.items()))
        if kind != "affinity":
            reporter.warn(f"{path.name}: unknown property {kind!r}; Boltz prediction docs focus on affinity.")
            continue
        if not isinstance(spec, dict):
            reporter.error(f"{path.name}: affinity property {index} must be a mapping.")
            continue
        binder = spec.get("binder")
        if not isinstance(binder, str) or not binder:
            reporter.error(f"{path.name}: affinity property {index} needs a binder chain id.")
            continue
        affinity_binders.append(binder)
        if binder not in ligand_ids:
            reporter.error(f"{path.name}: affinity binder {binder!r} is not a ligand chain id.")
        if binder in multi_copy_ligands:
            reporter.error(f"{path.name}: affinity binder {binder!r} belongs to a multi-copy ligand entry.")
    if len(set(affinity_binders)) > 1:
        reporter.error(f"{path.name}: only one affinity binder is currently supported.")


def validate_fasta(path: Path, args: argparse.Namespace, reporter: Reporter) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        reporter.error(f"{path.name}: FASTA file is not valid UTF-8 text.")
        return
    records = [chunk for chunk in text.split(">") if chunk.strip()]
    if not records:
        reporter.error(f"{path.name}: FASTA contains no records.")
        return
    seen: set[str] = set()
    has_auto_msa = False
    has_custom_msa = False
    for index, record in enumerate(records, start=1):
        lines = [line.strip() for line in record.splitlines() if line.strip()]
        if not lines:
            continue
        header = lines[0].split()[0]
        parts = header.split("|")
        if len(parts) < 2:
            reporter.error(f"{path.name}: FASTA record {index} header must be CHAIN_ID|ENTITY_TYPE|MSA_PATH.")
            continue
        chain_id, entity_type = parts[:2]
        if not chain_id:
            reporter.error(f"{path.name}: FASTA record {index} has empty chain id.")
        elif chain_id in seen:
            reporter.error(f"{path.name}: duplicate FASTA chain id {chain_id!r}.")
        seen.add(chain_id)
        entity_type = entity_type.lower()
        if entity_type not in {"protein", "dna", "rna", "ccd", "smiles"}:
            reporter.error(f"{path.name}: FASTA record {index} has invalid entity type {entity_type!r}.")
        sequence = "".join(lines[1:]).strip()
        if not sequence:
            reporter.error(f"{path.name}: FASTA record {index} has empty sequence/body.")
        if len(parts) >= 3 and parts[2]:
            if entity_type != "protein":
                reporter.error(f"{path.name}: MSA path in FASTA is only allowed for proteins.")
            elif parts[2].lower() != "empty":
                has_custom_msa = True
                validate_msa_path(parts[2], path, reporter)
            else:
                reporter.warn(f"{path.name}: FASTA record {index} uses single-sequence `empty` MSA mode.")
        elif entity_type == "protein":
            has_auto_msa = True
    if has_custom_msa and has_auto_msa:
        reporter.error(f"{path.name}: mixes custom and omitted FASTA protein MSA fields.")
    if has_auto_msa and not args.use_msa_server:
        reporter.error(f"{path.name}: has protein records without MSA; pass --use_msa_server to Boltz or add MSA paths.")
    reporter.warn(f"{path.name}: FASTA is deprecated; prefer YAML for new Boltz prediction inputs.")


def validate_a3m(path: Path, reporter: Reporter, nested: bool = False) -> None:
    try:
        if path.suffix.lower() == ".gz":
            import gzip

            with gzip.open(path, "rt", encoding="utf-8") as handle:
                lines = handle.readlines()
        else:
            lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"Could not read A3M {path}: {exc}")
        return
    headers = 0
    sequences = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            headers += 1
            continue
        sequences += 1
        normalized = stripped.replace("-", "").replace(".", "")
        if normalized and not set(normalized.upper()).issubset(PROTEIN_ALPHABET):
            reporter.warn(f"{path.name}: A3M contains unusual alignment characters.")
            break
    if headers == 0 or sequences == 0:
        reporter.error(f"{path.name}: A3M needs at least one header and sequence line.")
    elif not nested:
        reporter.note(f"{path.name}: A3M shape looks plausible ({headers} headers).")


def validate_csv(path: Path, reporter: Reporter, nested: bool = False) -> None:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            rows = list(reader)
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"Could not read CSV {path}: {exc}")
        return
    if sorted(columns) != ["key", "sequence"]:
        reporter.error(f"{path.name}: paired MSA CSV columns must be exactly `sequence,key`.")
    if not rows:
        reporter.error(f"{path.name}: paired MSA CSV has no rows.")
    for row_number, row in enumerate(rows[:5], start=2):
        if not (row.get("sequence") or "").strip():
            reporter.error(f"{path.name}: row {row_number} has an empty sequence.")
    if rows and not nested:
        reporter.note(f"{path.name}: paired MSA CSV shape looks plausible ({len(rows)} rows).")


def validate_auth(args: argparse.Namespace, reporter: Reporter) -> None:
    if not args.check_auth:
        return
    basic_user = args.msa_server_username or os.environ.get("BOLTZ_MSA_USERNAME")
    basic_password = args.msa_server_password or os.environ.get("BOLTZ_MSA_PASSWORD")
    api_value = args.api_key_value or os.environ.get("MSA_API_KEY_VALUE")
    has_basic = bool(basic_user or basic_password or args.basic_auth)
    has_complete_basic = bool((basic_user and basic_password) or args.basic_auth)
    has_api = bool(api_value or args.api_key or args.api_key_header)
    if has_basic and has_api:
        reporter.error("MSA auth conflict: use either basic auth or API-key auth, not both.")
    elif has_basic and not has_complete_basic:
        reporter.warn("Incomplete basic MSA auth: set both username and password.")
    elif has_complete_basic:
        reporter.note("MSA auth: basic auth selected; prefer environment variables for secrets.")
    elif has_api:
        reporter.note("MSA auth: API-key auth selected; prefer MSA_API_KEY_VALUE for the secret value.")


def validate_cache(reporter: Reporter) -> None:
    env_cache = os.environ.get("BOLTZ_CACHE")
    if env_cache and not Path(env_cache).expanduser().is_absolute():
        reporter.error(f"BOLTZ_CACHE must be an absolute path, got {env_cache!r}.")


def output_notes(files: list[Path], args: argparse.Namespace, reporter: Reporter) -> None:
    if not args.out_dir:
        return
    out_dir = Path(args.out_dir)
    for file_path in files:
        stem = file_path.stem
        prediction_dir = out_dir / "predictions" / stem
        if prediction_dir.exists() and not args.override:
            reporter.warn(
                f"Existing prediction directory {prediction_dir} may be skipped by Boltz; use --override to rerun."
            )
        reporter.note(f"Expected prediction folder: {prediction_dir}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Boltz prediction YAML/FASTA/MSA inputs without model downloads.",
    )
    parser.add_argument("data", type=Path, help="YAML/FASTA input file or directory, or standalone A3M/CSV MSA file.")
    msa_group = parser.add_mutually_exclusive_group()
    msa_group.add_argument("--use-msa-server", action="store_true", dest="use_msa_server", help="Validate as if boltz predict will use --use_msa_server.")
    msa_group.add_argument("--no-use-msa-server", action="store_false", dest="use_msa_server", help="Validate as if boltz predict will not use --use_msa_server.")
    parser.set_defaults(use_msa_server=False)
    parser.add_argument("--out-dir", help="Prediction output directory to check for stale output folders.")
    parser.add_argument("--override", action="store_true", help="Indicate that boltz predict will be run with --override.")
    parser.add_argument("--check-auth", action="store_true", help="Check MSA auth flags/environment for mutually exclusive methods.")
    parser.add_argument("--msa-server-username", help="Username that would be passed to --msa_server_username.")
    parser.add_argument("--msa-server-password", help="Password that would be passed to --msa_server_password.")
    parser.add_argument("--api-key-header", help="Header that would be passed to --api_key_header.")
    parser.add_argument("--api-key-value", help="Value that would be passed to --api_key_value.")
    parser.add_argument("--basic-auth", action="store_true", help="Declare that basic auth will be used without exposing secret values to this script.")
    parser.add_argument("--api-key", action="store_true", help="Declare that API-key auth will be used without exposing secret values to this script.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    reporter = Reporter()
    validate_cache(reporter)
    validate_auth(args, reporter)

    data = args.data
    suffixes = [suffix.lower() for suffix in data.suffixes]
    if data.exists() and (data.suffix.lower() == ".csv"):
        validate_csv(data, reporter)
        files: list[Path] = []
    elif data.exists() and (data.suffix.lower() == ".a3m" or suffixes[-2:] == [".a3m", ".gz"]):
        validate_a3m(data, reporter)
        files = []
    else:
        files = input_files(data, reporter)
        for file_path in files:
            suffix = file_path.suffix.lower()
            if suffix in {".yaml", ".yml"}:
                validate_yaml(file_path, args, reporter)
            elif suffix in {".fasta", ".fa", ".fas"}:
                validate_fasta(file_path, args, reporter)
        output_notes(files, args, reporter)

    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
