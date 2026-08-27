#!/usr/bin/env python3
"""Read-only validation for a BindCraft target JSON and optional PDB.

This helper intentionally has no BindCraft/source imports, network access, or
filesystem mutation.  It validates the target-settings contract and performs a
conservative chain/residue check when --pdb is supplied.  Biopython is used
when available; a small standard-library PDB reader keeps JSON/PDB inspection
usable in minimal environments.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REQUIRED_KEYS = (
    "design_path",
    "binder_name",
    "starting_pdb",
    "chains",
    "target_hotspot_residues",
    "lengths",
    "number_of_final_designs",
)
STANDARD_AA = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
    "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP",
    "TYR", "VAL",
}
# The documented BindCraft hotspot forms are numeric tokens/ranges, optionally
# prefixed by a single-character PDB chain ID, or a complete chain ID.
HOTSPOT_TOKEN = re.compile(
    r"^(?:(?P<chain>[A-Za-z])(?P<first>\d+)(?:-(?P<last>\d+))?|(?P<number>\d+)(?:-(?P<number_last>\d+))?|(?P<whole>[A-Za-z0-9]))$"
)


class ValidationError(Exception):
    """An input error that should produce a concise non-zero report."""


def _display_path(value: Any) -> str:
    """Return a path as supplied, without resolving or requiring it."""
    return str(value)


def _is_local_absolute(value: str) -> bool:
    """Identify any absolute path so it can be reported without resolving it."""
    return Path(value).is_absolute()


def load_target_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"target JSON does not exist: {path}") from exc
    except OSError as exc:
        raise ValidationError(f"cannot read target JSON {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"malformed JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise ValidationError("target JSON root must be an object")
    return data


def _validate_string(data: dict[str, Any], key: str, errors: list[str]) -> str | None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a non-empty string")
        return None
    return value.strip()


def parse_chain_list(value: str) -> list[str]:
    chains = [item.strip() for item in value.split(",") if item.strip()]
    if not chains or any(len(chain) != 1 for chain in chains):
        raise ValidationError("chains must be comma-separated one-character chain IDs")
    if len(set(chains)) != len(chains):
        raise ValidationError("chains contains a duplicate chain ID")
    return chains


def validate_schema(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))

    unknown = [key for key in data if key not in REQUIRED_KEYS]
    if unknown:
        warnings.append("unrecognized keys will not be used by this validator: " + ", ".join(unknown))

    design_path = _validate_string(data, "design_path", errors)
    binder_name = _validate_string(data, "binder_name", errors)
    starting_pdb = _validate_string(data, "starting_pdb", errors)
    chains_value = _validate_string(data, "chains", errors)

    if design_path is not None:
        if "\x00" in design_path:
            errors.append("design_path must not contain a NUL character")
        if _is_local_absolute(design_path):
            warnings.append(f"design_path is absolute; reported only and not resolved: {design_path}")
    if starting_pdb is not None:
        if "\x00" in starting_pdb:
            errors.append("starting_pdb must not contain a NUL character")
        if _is_local_absolute(starting_pdb):
            warnings.append(f"starting_pdb is absolute; reported only and not resolved: {starting_pdb}")
    if binder_name is not None:
        if any(char in binder_name for char in ("/", "\\", "\x00", "\n", "\r")):
            errors.append("binder_name must not contain path separators, control characters, or NUL")
    if chains_value is not None:
        try:
            parse_chain_list(chains_value)
        except ValidationError as exc:
            errors.append(str(exc))

    hotspot = data.get("target_hotspot_residues")
    if hotspot is not None and not isinstance(hotspot, str):
        errors.append("target_hotspot_residues must be JSON null or a string")
    elif isinstance(hotspot, str) and not hotspot.strip():
        warnings.append("target_hotspot_residues is an empty string; prefer JSON null for AF2 site selection")

    lengths = data.get("lengths")
    if (
        not isinstance(lengths, list)
        or len(lengths) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in lengths)
    ):
        errors.append("lengths must be a two-element array of integers")
    elif lengths[0] <= 0 or lengths[1] <= 0 or lengths[0] > lengths[1]:
        errors.append("lengths must contain positive values in [minimum, maximum] order")

    final_count = data.get("number_of_final_designs")
    if isinstance(final_count, bool) or not isinstance(final_count, int) or final_count <= 0:
        errors.append("number_of_final_designs must be a positive integer")

    return errors, warnings


def _record_from_fixed_width(line: str) -> tuple[str, str, str] | None:
    """Extract chain, residue number, insertion code from ATOM/HETATM text."""
    if not line.startswith(("ATOM  ", "HETATM")) or len(line) < 27:
        return None
    chain = line[21].strip() or "_"
    residue_name = line[17:20].strip().upper()
    number = line[22:26].strip()
    insertion = line[26].strip()
    if not number:
        return None
    try:
        int(number)
    except ValueError:
        return None
    return chain, f"{number}{insertion}", residue_name


def parse_pdb_stdlib(path: Path) -> dict[str, set[tuple[int, str]]]:
    chains: dict[str, set[tuple[int, str]]] = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                record = _record_from_fixed_width(line)
                if record is None:
                    continue
                chain, residue, residue_name = record
                if residue_name not in STANDARD_AA:
                    continue
                number = int(re.match(r"-?\d+", residue).group(0))
                insertion = residue[len(str(number)):]
                chains.setdefault(chain, set()).add((number, insertion))
    except FileNotFoundError as exc:
        raise ValidationError(f"PDB does not exist: {path}") from exc
    except OSError as exc:
        raise ValidationError(f"cannot read PDB {path}: {exc}") from exc
    return chains


def parse_pdb(path: Path) -> tuple[dict[str, set[tuple[int, str]]], str]:
    """Parse standard amino-acid residue IDs with Bio.PDB, then fallback."""
    try:
        from Bio.PDB import PDBParser  # optional third-party dependency only
    except ImportError:
        return parse_pdb_stdlib(path), "stdlib"

    try:
        structure = PDBParser(QUIET=True).get_structure("target", str(path))
        chains: dict[str, set[tuple[int, str]]] = {}
        for model in structure:
            for chain in model:
                for residue in chain:
                    name = residue.get_resname().strip().upper()
                    if name not in STANDARD_AA:
                        continue
                    number, insertion = residue.id[1], residue.id[2].strip()
                    if isinstance(number, int):
                        chains.setdefault(chain.id or "_", set()).add((number, insertion))
            # Model 0 is enough for a presence summary and avoids duplicate models.
            break
        return chains, "Biopython"
    except Exception as exc:  # parser exceptions vary across Biopython versions
        raise ValidationError(f"could not parse PDB {path}: {exc}") from exc


def _format_residue(number: int, insertion: str = "") -> str:
    return f"{number}{insertion}" if insertion else str(number)


def summarize_chains(chains: dict[str, set[tuple[int, str]]]) -> str:
    if not chains:
        return "PDB standard-amino-acid summary: no standard amino-acid residues found"
    lines = ["PDB standard-amino-acid summary:"]
    for chain in sorted(chains):
        residues = sorted(chains[chain])
        shown = ", ".join(_format_residue(n, ins) for n, ins in residues[:12])
        if len(residues) > 12:
            shown += ", ..."
        lines.append(f"  chain {chain}: {len(residues)} residues ({shown})")
    return "\n".join(lines)


def _residue_numbers(residues: set[tuple[int, str]]) -> set[int]:
    return {number for number, _ in residues}


def validate_hotspots(
    hotspot: str | None,
    selected_chains: list[str],
    pdb_chains: dict[str, set[tuple[int, str]]] | None,
) -> list[str]:
    errors: list[str] = []
    if hotspot is None or not hotspot.strip():
        return errors
    tokens = [token.strip() for token in hotspot.split(",")]
    if any(not token for token in tokens):
        return ["target_hotspot_residues contains an empty comma-separated token"]
    for token in tokens:
        match = HOTSPOT_TOKEN.fullmatch(token)
        if not match:
            errors.append(f"invalid hotspot token {token!r}; use 56, 56-60, A56-60, or A")
            continue
        whole = match.group("whole")
        chain = match.group("chain")
        if whole is not None:
            if whole not in selected_chains:
                errors.append(f"whole-chain hotspot {whole!r} is not in chains")
            if pdb_chains is not None and whole not in pdb_chains:
                errors.append(f"hotspot chain {whole!r} is absent from PDB")
            continue
        first_text = match.group("first") or match.group("number")
        last_text = match.group("last") or match.group("number_last") or first_text
        first, last = int(first_text), int(last_text)
        if first > last:
            errors.append(f"hotspot range {token!r} ends before it starts")
            continue
        target_chains = [chain] if chain else selected_chains
        if chain and chain not in selected_chains:
            errors.append(f"hotspot {token!r} names chain {chain!r}, which is not in chains")
        if pdb_chains is None:
            continue
        for target_chain in target_chains:
            if target_chain not in pdb_chains:
                errors.append(f"hotspot chain {target_chain!r} is absent from PDB")
                continue
            present = _residue_numbers(pdb_chains[target_chain])
            missing = [str(number) for number in range(first, last + 1) if number not in present]
            if missing:
                sample = ", ".join(missing[:10])
                suffix = "..." if len(missing) > 10 else ""
                errors.append(
                    f"hotspot {token!r} has residue numbers absent from chain {target_chain}: {sample}{suffix}"
                )
    return errors


def validate_pdb_selection(
    chains_value: str,
    hotspot: str | None,
    pdb_path: Path,
) -> tuple[list[str], str]:
    try:
        selected = parse_chain_list(chains_value)
    except ValidationError as exc:
        return [str(exc)], ""
    pdb_chains, parser_name = parse_pdb(pdb_path)
    errors: list[str] = []
    for chain in selected:
        if chain not in pdb_chains:
            errors.append(f"selected chain {chain!r} is absent from PDB")
    errors.extend(validate_hotspots(hotspot, selected, pdb_chains))
    return errors, summarize_chains(pdb_chains) + f"\nPDB parser: {parser_name}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only BindCraft target JSON and optional PDB validator."
    )
    parser.add_argument(
        "--target-json", required=True, type=Path, metavar="PATH",
        help="target settings JSON to validate (required)",
    )
    parser.add_argument(
        "--pdb", type=Path, metavar="PATH",
        help="optional PDB to summarize and compare with chains/hotspots",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = load_target_json(args.target_json)
        errors, warnings = validate_schema(data)
        print(f"Target JSON: {args.target_json}")
        print("Required keys: " + ", ".join(REQUIRED_KEYS))
        for key in ("design_path", "starting_pdb"):
            if key in data:
                print(f"Declared {key}: {_display_path(data[key])}")
                if isinstance(data[key], str) and _is_local_absolute(data[key]):
                    print(f"  NOTE: {key} looks repository/environment-specific; existence is not required by this check")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        chains_value = data.get("chains")
        if args.pdb is not None:
            if not isinstance(chains_value, str):
                errors.append("cannot inspect PDB selection until chains is a string")
            else:
                pdb_errors, summary = validate_pdb_selection(
                    chains_value, data.get("target_hotspot_residues"), args.pdb
                )
                if summary:
                    print(summary)
                errors.extend(pdb_errors)
        else:
            print("PDB: not supplied; chain and hotspot presence checks were skipped")

        if errors:
            print("Validation: FAILED")
            for error in errors:
                print(f"  - {error}")
            return 1
        print("Validation: PASSED (JSON/PDB input checks only)")
        return 0
    except ValidationError as exc:
        print(f"Validation: FAILED\n  - {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
