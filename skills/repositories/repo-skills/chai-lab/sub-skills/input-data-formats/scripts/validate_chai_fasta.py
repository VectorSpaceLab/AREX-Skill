#!/usr/bin/env python3
"""Validate Chai FASTA inputs without running full model inference."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Chai FASTA headers, entity names, sequence compatibility, "
            "and optionally Chai tokenization."
        )
    )
    parser.add_argument("fasta", type=Path, help="Input FASTA file for Chai")
    parser.add_argument(
        "--length-limit",
        type=int,
        default=None,
        help="Optional total raw sequence/SMILES character limit passed to read_inputs",
    )
    parser.add_argument(
        "--tokenize",
        action="store_true",
        help="Also run load_chains_from_raw to catch malformed ligands and chain mapping issues",
    )
    parser.add_argument(
        "--entity-names-as-subchains",
        action="store_true",
        help=(
            "Validate tokenization using FASTA entity names as Chai subchain IDs; "
            "matches run_inference(..., fasta_names_as_cif_chains=True)"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of text",
    )
    return parser


@dataclass
class RecordReport:
    index: int
    entity_type: str
    entity_name: str
    sequence_length: int
    possible_entity_types: list[str]
    messages: list[str]


@dataclass
class ValidationReport:
    fasta: str
    records: list[RecordReport]
    errors: list[str]
    warnings: list[str]
    tokenized_chains: int | None

    @property
    def ok(self) -> bool:
        return not self.errors


def import_chai_modules():
    try:
        from chai_lab.data.dataset.inference_dataset import load_chains_from_raw, read_inputs
        from chai_lab.data.parsing.input_validation import (
            constituents_of_modified_fasta,
            identify_potential_entity_types,
        )
        from chai_lab.data.parsing.structure.entity_type import EntityType
    except Exception as exc:
        raise RuntimeError(
            "Could not import chai_lab validation APIs. Install Chai Lab with "
            "its dependencies first, for example: pip install chai_lab==0.6.1. "
            f"Import error: {exc}"
        ) from exc
    return read_inputs, load_chains_from_raw, constituents_of_modified_fasta, identify_potential_entity_types, EntityType


def validate(args: argparse.Namespace) -> ValidationReport:
    fasta_path = args.fasta
    report = ValidationReport(
        fasta=str(fasta_path),
        records=[],
        errors=[],
        warnings=[],
        tokenized_chains=None,
    )

    try:
        read_inputs, load_chains_from_raw, constituents_of_modified_fasta, identify_potential_entity_types, EntityType = import_chai_modules()
    except RuntimeError as exc:
        report.errors.append(str(exc))
        return report

    if not fasta_path.exists():
        report.errors.append(f"FASTA file does not exist: {fasta_path}")
        return report
    if not fasta_path.is_file():
        report.errors.append(f"FASTA path is not a file: {fasta_path}")
        return report

    try:
        inputs = read_inputs(fasta_path, length_limit=args.length_limit)
    except Exception as exc:
        report.errors.append(f"Chai read_inputs failed: {exc}")
        return report

    if not inputs:
        report.errors.append("No FASTA records were parsed")
        return report

    name_counts = Counter(input_item.entity_name for input_item in inputs)
    duplicate_names = sorted(name for name, count in name_counts.items() if count > 1)
    if duplicate_names:
        report.errors.append(
            "Duplicate entity names are not allowed for inference: "
            + ", ".join(duplicate_names)
        )

    for index, input_item in enumerate(inputs, start=1):
        entity_type = EntityType(input_item.entity_type)
        possible_types = identify_potential_entity_types(input_item.sequence)
        possible_names = [possible_type.name for possible_type in possible_types]
        messages: list[str] = []

        if entity_type not in possible_types:
            if possible_names:
                messages.append(
                    "sequence heuristic suggests "
                    + "/".join(possible_names)
                    + f", not {entity_type.name}"
                )
            else:
                messages.append("sequence did not match any Chai input-type heuristic")

        if entity_type.name in {"PROTEIN", "DNA", "RNA"}:
            constituents = constituents_of_modified_fasta(input_item.sequence)
            if constituents is None:
                messages.append("modified-FASTA polymer syntax is malformed")
            elif not constituents:
                messages.append("polymer sequence has no residues")

        if args.entity_names_as_subchains:
            if not input_item.entity_name.isascii():
                messages.append("entity name is not ASCII but will be used as a subchain ID")
            if len(input_item.entity_name) > 4:
                messages.append(
                    "entity name is longer than 4 characters and may fail Chai subchain tensor encoding"
                )

        report.records.append(
            RecordReport(
                index=index,
                entity_type=entity_type.name,
                entity_name=input_item.entity_name,
                sequence_length=len(input_item.sequence),
                possible_entity_types=possible_names,
                messages=messages,
            )
        )
        report.warnings.extend(
            f"record {index} ({entity_type.name}|{input_item.entity_name}): {message}"
            for message in messages
        )

    if args.tokenize:
        try:
            chains = load_chains_from_raw(
                inputs,
                entity_name_as_subchain=args.entity_names_as_subchains,
            )
        except Exception as exc:
            report.errors.append(f"Chai load_chains_from_raw failed: {exc}")
        else:
            report.tokenized_chains = len(chains)
            if len(chains) != len(inputs):
                report.errors.append(
                    f"Tokenization produced {len(chains)} chains from {len(inputs)} records; "
                    "one or more records were dropped"
                )

    return report


def emit_text(report: ValidationReport) -> None:
    status = "OK" if report.ok else "FAILED"
    print(f"Chai FASTA validation: {status}")
    print(f"File: {report.fasta}")
    print(f"Records: {len(report.records)}")
    for record in report.records:
        possible = "/".join(record.possible_entity_types) or "none"
        print(
            f"- #{record.index} {record.entity_type}|{record.entity_name}: "
            f"length={record.sequence_length}, possible={possible}"
        )
        for message in record.messages:
            print(f"  warning: {message}")
    if report.tokenized_chains is not None:
        print(f"Tokenized chains: {report.tokenized_chains}")
    for warning in report.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = validate(args)
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        emit_text(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
