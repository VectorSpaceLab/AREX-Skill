#!/usr/bin/env python3
"""Validate DGL-LifeSci WLN reaction input text files without training or downloads."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

VALID_CHANGE_TYPES = {"0", "0.0", "1", "1.0", "2", "2.0", "3", "3.0", "1.5"}
ATOM_MAP_RE = re.compile(r":([1-9][0-9]*)")
CANDIDATE_RE = re.compile(
    r"^\s*(?P<a1>[1-9][0-9]*)\s+"
    r"(?P<a2>[1-9][0-9]*)\s+"
    r"(?P<change>0(?:\.0)?|1(?:\.0|\.5)?|2(?:\.0)?|3(?:\.0)?)\s+"
    r"(?P<score>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)


class ValidationError(Exception):
    """Raised when a row fails validation."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate reaction SMILES text files and optional candidate-bond "
            "files for DGL-LifeSci WLN reaction prediction. The script performs only "
            "text-level checks and never imports DGL, Torch, RDKit, or dgllife."
        )
    )
    parser.add_argument(
        "--reactions",
        required=True,
        type=Path,
        help="Raw reaction file or processed reaction+graph-edit file to validate.",
    )
    parser.add_argument(
        "--candidate-bonds",
        type=Path,
        default=None,
        help="Optional candidate-bond file aligned one-to-one with reactions.",
    )
    parser.add_argument(
        "--processed",
        action="store_true",
        help="Expect each reaction row to contain graph edits after the reaction string.",
    )
    parser.add_argument(
        "--require-atom-maps",
        action="store_true",
        help="Require atom-map markers such as :1 in each reaction string.",
    )
    parser.add_argument(
        "--check-consecutive-maps",
        action="store_true",
        help="Warn when atom-map numbers are not consecutive from 1.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=0,
        help="Validate at most this many non-empty rows. Use 0 for all rows.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=10000,
        help="Warn when a reaction string is longer than this many characters.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Stop after reporting this many errors.",
    )
    return parser.parse_args(argv)


def read_limited_lines(
    path: Path, max_rows: int, *, keep_blank: bool = False
) -> List[Tuple[int, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    rows: List[Tuple[int, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.rstrip("\n\r")
            if not keep_blank and not stripped.strip():
                continue
            rows.append((line_number, stripped))
            if max_rows and len(rows) >= max_rows:
                break
    return rows


def split_reaction_and_edits(row: str, processed: bool) -> Tuple[str, Optional[str]]:
    if not processed:
        return row.strip(), None
    parts = row.split()
    if len(parts) != 2:
        raise ValidationError(
            "processed rows must contain exactly two whitespace-separated fields: "
            "reaction and graph_edits"
        )
    return parts[0], parts[1]


def validate_reaction_structure(reaction: str, require_atom_maps: bool) -> List[int]:
    if reaction.count(">>") != 1:
        raise ValidationError("reaction must contain exactly one '>>' separator")
    if any(char.isspace() for char in reaction):
        raise ValidationError("reaction string must not contain whitespace")

    reactants, products = reaction.split(">>")
    if not reactants:
        raise ValidationError("reactants side is empty")
    if not products:
        raise ValidationError("products side is empty")
    if reactants.startswith(".") or reactants.endswith(".") or ".." in reactants:
        raise ValidationError("reactants contain an empty molecule around '.' separators")
    if products.startswith(".") or products.endswith(".") or ".." in products:
        raise ValidationError("products contain an empty molecule around '.' separators")

    maps = [int(match.group(1)) for match in ATOM_MAP_RE.finditer(reaction)]
    if require_atom_maps and not maps:
        raise ValidationError("no atom-map markers like ':1' were found")
    return maps


def validate_graph_edits(graph_edits: Optional[str]) -> int:
    if graph_edits is None:
        return 0
    edits = [item for item in graph_edits.split(";") if item]
    if not edits:
        raise ValidationError("processed row has no graph edits")
    for edit in edits:
        fields = edit.split("-")
        if len(fields) != 3:
            raise ValidationError(f"graph edit '{edit}' must be atom1-atom2-change_type")
        atom1, atom2, change = fields
        if not atom1.isdigit() or int(atom1) <= 0:
            raise ValidationError(f"graph edit '{edit}' has invalid atom1")
        if not atom2.isdigit() or int(atom2) <= 0:
            raise ValidationError(f"graph edit '{edit}' has invalid atom2")
        if change not in VALID_CHANGE_TYPES:
            raise ValidationError(f"graph edit '{edit}' has unsupported change type")
    return len(edits)


def validate_candidate_line(row: str) -> int:
    records = [record for record in row.split(";") if record.strip()]
    for record in records:
        match = CANDIDATE_RE.match(record)
        if match is None:
            raise ValidationError(
                "candidate record must be 'atom1 atom2 change_type score' with positive atom ids"
            )
        atom1 = int(match.group("a1"))
        atom2 = int(match.group("a2"))
        if atom1 == atom2:
            raise ValidationError("candidate atom ids must refer to two different atoms")
        if match.group("change") not in VALID_CHANGE_TYPES:
            raise ValidationError("candidate has unsupported change type")
    return len(records)


def warn_nonconsecutive_maps(maps: Iterable[int]) -> Optional[str]:
    unique_maps = sorted(set(maps))
    if not unique_maps:
        return None
    expected = list(range(1, unique_maps[-1] + 1))
    if unique_maps != expected:
        missing = sorted(set(expected) - set(unique_maps))
        preview = ",".join(str(value) for value in missing[:8])
        suffix = "..." if len(missing) > 8 else ""
        return f"atom maps are not consecutive from 1; missing {preview}{suffix}"
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    errors: List[str] = []
    warnings: List[str] = []
    reaction_count = 0
    processed_edit_count = 0
    long_reaction_count = 0

    try:
        reaction_rows = read_limited_lines(args.reactions, args.max_rows)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for line_number, row in reaction_rows:
        try:
            reaction, graph_edits = split_reaction_and_edits(row, args.processed)
            maps = validate_reaction_structure(reaction, args.require_atom_maps)
            processed_edit_count += validate_graph_edits(graph_edits)
            if args.max_length and len(reaction) > args.max_length:
                long_reaction_count += 1
                warnings.append(
                    f"{args.reactions}:{line_number}: reaction length {len(reaction)} exceeds {args.max_length}"
                )
            if args.check_consecutive_maps:
                map_warning = warn_nonconsecutive_maps(maps)
                if map_warning:
                    warnings.append(f"{args.reactions}:{line_number}: {map_warning}")
            reaction_count += 1
        except ValidationError as exc:
            errors.append(f"{args.reactions}:{line_number}: {exc}")
            if len(errors) >= args.max_errors:
                break

    candidate_count = 0
    candidate_record_count = 0
    if args.candidate_bonds is not None and len(errors) < args.max_errors:
        try:
            candidate_rows = read_limited_lines(
                args.candidate_bonds, args.max_rows, keep_blank=True
            )
        except OSError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if len(candidate_rows) != len(reaction_rows):
            errors.append(
                f"{args.candidate_bonds}: row count {len(candidate_rows)} does not match "
                f"reaction row count {len(reaction_rows)}"
            )
        for line_number, row in candidate_rows:
            try:
                candidate_record_count += validate_candidate_line(row)
                candidate_count += 1
            except ValidationError as exc:
                errors.append(f"{args.candidate_bonds}:{line_number}: {exc}")
                if len(errors) >= args.max_errors:
                    break

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    print(f"reaction_rows={reaction_count}")
    if args.processed:
        print(f"graph_edits={processed_edit_count}")
    if long_reaction_count:
        print(f"long_reaction_rows={long_reaction_count}")
    if args.candidate_bonds is not None:
        print(f"candidate_rows={candidate_count}")
        print(f"candidate_records={candidate_record_count}")
    print(f"warnings={len(warnings)}")
    print(f"errors={len(errors)}")

    if errors:
        return 1
    if reaction_count == 0:
        print("ERROR: no non-empty reaction rows found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
