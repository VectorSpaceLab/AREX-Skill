#!/usr/bin/env python3
"""Validate Chai-1 restraint CSVs and optional FASTA chain alignment."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from string import ascii_uppercase
from typing import Any, Callable


@dataclass(frozen=True)
class FastaRecord:
    entity_type: str
    entity_name: str
    sequence: str
    chain_id: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Chai-1 restraint CSV with Chai's parser and optional "
            "FASTA chain/residue/glycan sanity checks. This does not run inference."
        )
    )
    parser.add_argument("restraints_csv", type=Path, help="Path to restraint CSV")
    parser.add_argument(
        "--fasta",
        type=Path,
        help="Optional Chai FASTA to check chain names, simple residues, and glycans",
    )
    parser.add_argument(
        "--fasta-names-as-cif-chains",
        action="store_true",
        help="Use FASTA entity names as chain IDs instead of automatic A/B/C IDs",
    )
    parser.add_argument(
        "--write-normalized",
        type=Path,
        help="Optional output CSV rewritten through chai_lab write_pairwise_table",
    )
    parser.add_argument(
        "--allow-covalent-without-atoms",
        action="store_true",
        help=(
            "Only warn, rather than fail, when covalent rows omit atom names. "
            "Chai feature building normally requires atoms on both sides."
        ),
    )
    return parser.parse_args()


def synth_chain_id(index: int) -> str:
    letters = len(ascii_uppercase)
    value = index
    result = ""
    while value >= 0:
        result = ascii_uppercase[value % letters] + result
        value = value // letters - 1
    return result


def read_simple_chai_fasta(path: Path, use_entity_names: bool) -> list[FastaRecord]:
    records: list[tuple[str, list[str]]] = []
    header: str | None = None
    seq_lines: list[str] = []

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, seq_lines))
            header = line[1:].strip()
            seq_lines = []
        else:
            if header is None:
                raise ValueError("FASTA sequence encountered before first header")
            seq_lines.append(line)
    if header is not None:
        records.append((header, seq_lines))

    if not records:
        raise ValueError("No FASTA records found")

    parsed: list[FastaRecord] = []
    seen_names: set[str] = set()
    for index, (record_header, record_seq_lines) in enumerate(records):
        entity_type, *parts = record_header.split("|")
        entity_type = entity_type.lower().strip()
        if entity_type not in {"protein", "ligand", "rna", "dna", "glycan"}:
            raise ValueError(f"Unsupported Chai FASTA entity type: {entity_type!r}")
        if len(parts) != 1:
            raise ValueError(
                "Chai FASTA headers should look like `>protein|name` or "
                f"`>protein|name=...`; got {record_header!r}"
            )
        label = parts[0].strip()
        if "=" in label:
            field, entity_name = label.split("=", 1)
            if field != "name":
                raise ValueError(f"Unsupported FASTA header field {field!r}")
        else:
            entity_name = label
        if not entity_name:
            raise ValueError(f"Missing entity name in FASTA header {record_header!r}")
        if entity_name in seen_names:
            raise ValueError(f"Duplicate FASTA entity name {entity_name!r}")
        seen_names.add(entity_name)

        sequence = "".join(record_seq_lines).strip()
        if not sequence:
            raise ValueError(f"Empty sequence for FASTA entity {entity_name!r}")
        chain_id = entity_name if use_entity_names else synth_chain_id(index)
        parsed.append(FastaRecord(entity_type, entity_name, sequence, chain_id))
    return parsed


def side_values(interaction: Any, side: str) -> tuple[str, str, str, str, int]:
    if side == "A":
        return (
            interaction.chainA,
            interaction.res_idxA,
            interaction.atom_nameA,
            interaction.res_idxA_name,
            interaction.res_idxA_pos,
        )
    if side == "B":
        return (
            interaction.chainB,
            interaction.res_idxB,
            interaction.atom_nameB,
            interaction.res_idxB_name,
            interaction.res_idxB_pos,
        )
    raise ValueError(side)


def check_covalent_atoms(
    interactions: list[Any], allow_missing: bool
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for row_num, interaction in enumerate(interactions, start=2):
        if getattr(interaction.connection_type, "value", interaction.connection_type) != "covalent":
            continue
        if interaction.atom_nameA and interaction.atom_nameB:
            continue
        message = (
            f"row {row_num}: covalent restraints should include atom names on both "
            f"sides; got res_idxA={interaction.res_idxA!r}, atomA={interaction.atom_nameA!r}, "
            f"res_idxB={interaction.res_idxB!r}, atomB={interaction.atom_nameB!r}"
        )
        if allow_missing:
            warnings.append(message)
        else:
            errors.append(message)
    return errors, warnings


def check_fasta(
    interactions: list[Any],
    fasta_path: Path,
    use_entity_names: bool,
    glycan_string_residues: Callable[[str], list[Any]],
) -> tuple[list[str], list[str], list[FastaRecord]]:
    errors: list[str] = []
    warnings: list[str] = []
    records = read_simple_chai_fasta(fasta_path, use_entity_names)
    chain_to_record = {record.chain_id: record for record in records}

    for record in records:
        if record.entity_type != "glycan":
            continue
        try:
            residues = glycan_string_residues(record.sequence)
        except Exception as exc:
            errors.append(
                f"glycan FASTA entity {record.entity_name!r} failed glycan parsing: {exc}"
            )
        else:
            warnings.append(
                f"glycan FASTA entity {record.entity_name!r} parsed as {len(residues)} sugar residue(s)"
            )

    for row_num, interaction in enumerate(interactions, start=2):
        for side in ("A", "B"):
            chain_id, residue_token, _atom_name, residue_name, residue_pos = side_values(
                interaction, side
            )
            record = chain_to_record.get(chain_id)
            if record is None:
                expected = ", ".join(chain_to_record)
                errors.append(
                    f"row {row_num} side {side}: chain {chain_id!r} is not in FASTA-derived "
                    f"chain IDs [{expected}]"
                )
                continue
            if not residue_token:
                continue
            if record.entity_type not in {"protein", "rna", "dna"}:
                warnings.append(
                    f"row {row_num} side {side}: skipping residue-letter check for "
                    f"{record.entity_type} chain {chain_id!r}"
                )
                continue
            if "(" in record.sequence or ")" in record.sequence:
                warnings.append(
                    f"row {row_num} side {side}: skipping raw residue-position check for "
                    f"modified sequence in chain {chain_id!r}"
                )
                continue
            if residue_pos > len(record.sequence):
                errors.append(
                    f"row {row_num} side {side}: residue position {residue_pos} exceeds "
                    f"chain {chain_id!r} length {len(record.sequence)}"
                )
                continue
            actual = record.sequence[residue_pos - 1].upper()
            if residue_name and actual != residue_name.upper():
                errors.append(
                    f"row {row_num} side {side}: residue token {residue_token!r} does not "
                    f"match FASTA chain {chain_id!r} at 1-based position {residue_pos} "
                    f"({actual!r})"
                )
    return errors, warnings, records


def summarize(interactions: list[Any]) -> str:
    counts = Counter(interaction.connection_type.value for interaction in interactions)
    parts = [f"{key}={counts.get(key, 0)}" for key in ("contact", "pocket", "covalent")]
    return f"parsed {len(interactions)} restraint row(s): " + ", ".join(parts)


def main() -> int:
    args = parse_args()

    try:
        from chai_lab.data.parsing.glycans import glycan_string_residues
        from chai_lab.data.parsing.restraints import parse_pairwise_table, write_pairwise_table
    except Exception as exc:
        print(
            "ERROR: could not import chai_lab restraint/glycan parsers. "
            "Install Chai-1 first, for example `pip install chai_lab==0.6.1`.",
            file=sys.stderr,
        )
        print(f"Import detail: {exc}", file=sys.stderr)
        return 2

    try:
        interactions = parse_pairwise_table(args.restraints_csv)
    except Exception as exc:
        print(f"ERROR: restraint parser rejected {args.restraints_csv}: {exc}", file=sys.stderr)
        return 1

    errors, warnings = check_covalent_atoms(
        interactions, allow_missing=args.allow_covalent_without_atoms
    )
    records: list[FastaRecord] = []
    if args.fasta is not None:
        try:
            fasta_errors, fasta_warnings, records = check_fasta(
                interactions,
                args.fasta,
                args.fasta_names_as_cif_chains,
                glycan_string_residues,
            )
        except Exception as exc:
            errors.append(f"FASTA validation failed: {exc}")
        else:
            errors.extend(fasta_errors)
            warnings.extend(fasta_warnings)

    if args.write_normalized and not errors:
        try:
            write_pairwise_table(interactions, args.write_normalized)
        except Exception as exc:
            errors.append(f"could not write normalized CSV {args.write_normalized}: {exc}")

    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {summarize(interactions)}")
    if records:
        mode = "FASTA entity names" if args.fasta_names_as_cif_chains else "automatic A/B/C IDs"
        chain_summary = ", ".join(
            f"{record.chain_id}:{record.entity_type}:{record.entity_name}" for record in records
        )
        print(f"OK: checked FASTA chains using {mode}: {chain_summary}")
    if args.write_normalized:
        print(f"OK: wrote normalized CSV to {args.write_normalized}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
