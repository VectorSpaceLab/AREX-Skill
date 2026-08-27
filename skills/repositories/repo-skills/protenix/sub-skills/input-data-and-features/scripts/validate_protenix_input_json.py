#!/usr/bin/env python3
"""Static validator for Protenix input JSON.

The validator checks common shape, entity, path, covalent-bond, and constraint
mistakes. It does not import Protenix, parse structures, call RDKit, or run
model inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ENTITY_TYPES = {"proteinChain", "dnaSequence", "rnaSequence", "ligand", "ion"}
POLYMER_TYPES = {"proteinChain", "dnaSequence", "rnaSequence"}
PATH_FIELDS = {"pairedMsaPath", "unpairedMsaPath", "templatesPath"}
LEGACY_BOND_FIELDS = {"left_entity", "right_entity", "left_copy", "right_copy", "left_position", "right_position", "left_atom", "right_atom"}
NEW_BOND_FIELDS = {"entity1", "entity2", "position1", "position2", "atom1", "atom2"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def entity_numbers(job: dict[str, Any]) -> set[str]:
    return {str(index + 1) for index, _ in enumerate(job.get("sequences", []))}


def validate_count_and_ids(path: str, entity: dict[str, Any], reporter: Reporter) -> None:
    count = entity.get("count")
    if count is None:
        reporter.warn(f"{path}: missing count; Protenix examples normally include count.")
    elif not isinstance(count, int) or count < 1:
        reporter.error(f"{path}: count must be a positive integer.")
    ids = entity.get("id")
    if ids is not None:
        if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
            reporter.error(f"{path}: id must be a list of strings when present.")
        elif isinstance(count, int) and len(ids) != count:
            reporter.error(f"{path}: id length must equal count.")


def validate_file_path(path: str, value: str, base: Path, check_paths: bool, reporter: Reporter) -> None:
    if not isinstance(value, str) or not value:
        reporter.error(f"{path}: path value must be a non-empty string.")
        return
    file_path = value[5:] if value.startswith("FILE_") else value
    candidate = Path(file_path)
    if not candidate.is_absolute():
        reporter.warn(f"{path}: relative path detected; Protenix docs recommend absolute paths for reusable JSON.")
        candidate = base / candidate
    if check_paths and not candidate.exists():
        reporter.error(f"{path}: referenced path does not exist: {file_path}")


def validate_modifications(path: str, entity_type: str, entity: dict[str, Any], reporter: Reporter) -> None:
    mods = entity.get("modifications")
    if mods is None:
        return
    if not isinstance(mods, list):
        reporter.error(f"{path}.modifications: must be a list.")
        return
    for index, mod in enumerate(mods):
        mod_path = f"{path}.modifications[{index}]"
        if not isinstance(mod, dict):
            reporter.error(f"{mod_path}: must be an object.")
            continue
        if entity_type == "proteinChain":
            if "ptmType" not in mod or "ptmPosition" not in mod:
                reporter.error(f"{mod_path}: protein modifications require ptmType and ptmPosition.")
        elif entity_type in {"dnaSequence", "rnaSequence"}:
            if "modificationType" not in mod or "basePosition" not in mod:
                reporter.error(f"{mod_path}: nucleotide modifications require modificationType and basePosition.")


def validate_entity(job_index: int, entity_index: int, wrapper: Any, base: Path, check_paths: bool, reporter: Reporter) -> None:
    wrapper_path = f"jobs[{job_index}].sequences[{entity_index}]"
    if not isinstance(wrapper, dict) or len(wrapper) != 1:
        reporter.error(f"{wrapper_path}: each sequence entry must be an object with exactly one entity type key.")
        return
    entity_type = next(iter(wrapper))
    entity = wrapper[entity_type]
    entity_path = f"{wrapper_path}.{entity_type}"
    if entity_type not in ENTITY_TYPES:
        reporter.error(f"{wrapper_path}: unknown entity type {entity_type!r}; expected one of {sorted(ENTITY_TYPES)}.")
        return
    if not isinstance(entity, dict):
        reporter.error(f"{entity_path}: entity payload must be an object.")
        return

    validate_count_and_ids(entity_path, entity, reporter)
    validate_modifications(entity_path, entity_type, entity, reporter)

    if entity_type in POLYMER_TYPES:
        if not isinstance(entity.get("sequence"), str) or not entity.get("sequence"):
            reporter.error(f"{entity_path}: sequence must be a non-empty string.")
        if "msa" in entity:
            reporter.warn(f"{entity_path}.msa: legacy msa dictionary is still accepted but pairedMsaPath/unpairedMsaPath are preferred.")
        for field in PATH_FIELDS:
            if field in entity:
                validate_file_path(f"{entity_path}.{field}", entity[field], base, check_paths, reporter)
    elif entity_type == "ligand":
        ligand = entity.get("ligand")
        if not isinstance(ligand, str) or not ligand:
            reporter.error(f"{entity_path}.ligand: ligand must be a non-empty CCD_, FILE_, or SMILES string.")
        elif ligand.startswith("FILE_"):
            validate_file_path(f"{entity_path}.ligand", ligand, base, check_paths, reporter)
        elif ligand.startswith("CCD_"):
            pass
        elif len(ligand) <= 3 and ligand.isalpha():
            reporter.warn(f"{entity_path}.ligand: short alphabetic ligand lacks CCD_ prefix; ions belong under ion, ligands usually use CCD_, FILE_, or SMILES.")
    elif entity_type == "ion":
        ion = entity.get("ion")
        if not isinstance(ion, str) or not ion:
            reporter.error(f"{entity_path}.ion: ion must be a non-empty code such as MG or NA.")
        elif ion.startswith("CCD_"):
            reporter.warn(f"{entity_path}.ion: ion codes should not use the CCD_ prefix.")


def validate_bonds(job_index: int, job: dict[str, Any], reporter: Reporter) -> None:
    bonds = job.get("covalent_bonds", [])
    if bonds in (None, []):
        return
    if not isinstance(bonds, list):
        reporter.error(f"jobs[{job_index}].covalent_bonds: must be a list.")
        return
    valid_entities = entity_numbers(job)
    for index, bond in enumerate(bonds):
        path = f"jobs[{job_index}].covalent_bonds[{index}]"
        if not isinstance(bond, dict):
            reporter.error(f"{path}: bond must be an object.")
            continue
        if LEGACY_BOND_FIELDS & set(bond):
            reporter.warn(f"{path}: legacy left_/right_ bond fields are accepted but entity1/entity2 style is preferred.")
        if not (NEW_BOND_FIELDS <= set(bond)) and not (LEGACY_BOND_FIELDS & set(bond)):
            reporter.error(f"{path}: expected new fields entity1/entity2/position1/position2/atom1/atom2 or legacy left_/right_ fields.")
        for field in ("entity1", "entity2"):
            if field in bond and str(bond[field]) not in valid_entities:
                reporter.error(f"{path}.{field}: references entity {bond[field]!r}, but valid entity numbers are {sorted(valid_entities)}.")
        has_copy1 = "copy1" in bond
        has_copy2 = "copy2" in bond
        if has_copy1 != has_copy2:
            reporter.error(f"{path}: copy1 and copy2 must be provided together or omitted together.")


def validate_constraints(job_index: int, job: dict[str, Any], reporter: Reporter) -> None:
    constraints = job.get("constraint")
    if constraints is None:
        return
    if not isinstance(constraints, (dict, list)):
        reporter.error(f"jobs[{job_index}].constraint: must be an object or list depending on constraint version.")
        return
    text = json.dumps(constraints, sort_keys=True)
    valid_entities = entity_numbers(job)
    for key in ("entity", "entity1", "entity2", "chain", "chain1", "chain2"):
        if f'"{key}"' in text:
            break
    if not valid_entities:
        reporter.error(f"jobs[{job_index}].constraint: cannot validate constraints without sequences.")


def validate_document(data: Any, base: Path, check_paths: bool) -> Reporter:
    reporter = Reporter()
    if not isinstance(data, list):
        reporter.error("Top-level JSON must be a list of job objects, even for one job.")
        return reporter
    if not data:
        reporter.error("Top-level job list must not be empty.")
        return reporter
    for job_index, job in enumerate(data):
        path = f"jobs[{job_index}]"
        if not isinstance(job, dict):
            reporter.error(f"{path}: job must be an object.")
            continue
        if not isinstance(job.get("name"), str) or not job.get("name"):
            reporter.warn(f"{path}.name: missing or empty name.")
        sequences = job.get("sequences")
        if not isinstance(sequences, list) or not sequences:
            reporter.error(f"{path}.sequences: must be a non-empty list.")
            continue
        for entity_index, entity in enumerate(sequences):
            validate_entity(job_index, entity_index, entity, base, check_paths, reporter)
        validate_bonds(job_index, job, reporter)
        validate_constraints(job_index, job, reporter)
    return reporter


def main() -> int:
    parser = argparse.ArgumentParser(description="Statically validate Protenix input JSON.")
    parser.add_argument("json_path", help="Path to a Protenix input JSON file.")
    parser.add_argument("--check-paths", action="store_true", help="Require referenced local files to exist.")
    parser.add_argument("--json", action="store_true", help="Emit diagnostics as JSON.")
    args = parser.parse_args()

    path = Path(args.json_path)
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - report any JSON/read failure clearly
        result = {"ok": False, "errors": [f"Could not read/parse JSON: {exc}"], "warnings": []}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result["errors"][0])
        return 2

    reporter = validate_document(data, path.parent, args.check_paths)
    result = {"ok": not reporter.errors, "errors": reporter.errors, "warnings": reporter.warnings}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for message in reporter.errors:
            print(f"ERROR: {message}")
        for message in reporter.warnings:
            print(f"WARNING: {message}")
        if result["ok"]:
            print("OK: no blocking static validation errors found.")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
