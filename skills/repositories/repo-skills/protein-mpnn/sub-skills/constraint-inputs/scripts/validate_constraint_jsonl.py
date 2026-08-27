#!/usr/bin/env python3
"""Validate ProteinMPNN constraint JSONL files without importing ProteinMPNN."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ALPHABET = "ACDEFGHIKLMNPQRSTVWYX"


class ValidationError(Exception):
    pass


def load_json_lines(path: str | None, label: str) -> list[Any]:
    if not path:
        return []
    items: list[Any] = []
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                items.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{label}: invalid JSON on line {line_number}: {exc}") from exc
    if not items:
        raise ValidationError(f"{label}: file has no non-empty JSON lines")
    return items


def load_single_dict(path: str | None, label: str) -> dict[str, Any] | None:
    if not path:
        return None
    items = load_json_lines(path, label)
    if len(items) != 1:
        raise ValidationError(
            f"{label}: expected exactly one JSON object line, found {len(items)}; "
            "helper-generated constraint JSONL files are usually single-line dictionaries"
        )
    if not isinstance(items[0], dict):
        raise ValidationError(f"{label}: top-level JSON value must be an object")
    return items[0]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def parsed_targets(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    targets: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(load_json_lines(path, "parsed"), start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"parsed: line {index} must be a JSON object")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise ValidationError(f"parsed: line {index} missing non-empty string field 'name'")
        if name in targets:
            raise ValidationError(f"parsed: duplicate target name {name!r}")
        chains = chain_lengths(item)
        if not chains:
            raise ValidationError(f"parsed:{name}: no seq_chain_<chain> keys found")
        targets[name] = item
    return targets


def chain_lengths(target: dict[str, Any]) -> dict[str, int]:
    lengths: dict[str, int] = {}
    for key, value in target.items():
        if key.startswith("seq_chain_") and isinstance(value, str):
            chain = key[len("seq_chain_") :]
            if chain:
                lengths[chain] = len(value)
    return lengths


def require_known_target(targets: dict[str, dict[str, Any]], label: str, name: str) -> dict[str, int]:
    if not targets:
        return {}
    if name not in targets:
        raise ValidationError(f"{label}: target {name!r} is not present in parsed JSONL")
    return chain_lengths(targets[name])


def check_chain(chain_lengths_map: dict[str, int], label: str, target_name: str, chain: Any) -> int | None:
    if not isinstance(chain, str) or not chain:
        raise ValidationError(f"{label}:{target_name}: chain keys must be non-empty strings")
    if chain_lengths_map and chain not in chain_lengths_map:
        raise ValidationError(f"{label}:{target_name}: chain {chain!r} is not present in parsed target")
    return chain_lengths_map.get(chain)


def check_positions(positions: Any, length: int | None, label: str) -> None:
    if not isinstance(positions, list):
        raise ValidationError(f"{label}: positions must be a list")
    for position in positions:
        if not positive_int(position):
            raise ValidationError(f"{label}: position {position!r} is not a positive integer")
        if length is not None and position > length:
            raise ValidationError(f"{label}: position {position} exceeds parsed chain length {length}")


def check_matrix(matrix: Any, rows: int | None, columns: int, label: str, probability_like: bool = False) -> None:
    if not isinstance(matrix, list):
        raise ValidationError(f"{label}: expected a list of rows")
    if rows is not None and len(matrix) != rows:
        raise ValidationError(f"{label}: expected {rows} rows, found {len(matrix)}")
    for row_index, row in enumerate(matrix, start=1):
        if not isinstance(row, list) or len(row) != columns:
            raise ValidationError(f"{label}: row {row_index} must contain {columns} numeric values")
        for value in row:
            if not is_number(value):
                raise ValidationError(f"{label}: row {row_index} contains non-numeric value {value!r}")
        if probability_like:
            row_sum = sum(float(value) for value in row)
            if row_sum < -1e-6:
                raise ValidationError(f"{label}: row {row_index} has a negative sum")
            if any(float(value) < -1e-8 for value in row):
                raise ValidationError(f"{label}: row {row_index} contains a negative probability")
            if row_sum and abs(row_sum - 1.0) > 1e-3:
                print(f"warning: {label}: row {row_index} sums to {row_sum:.6g}, not 1.0", file=sys.stderr)


def validate_chain_id(data: dict[str, Any] | None, targets: dict[str, dict[str, Any]]) -> None:
    if data is None:
        return
    for name, assignment in data.items():
        lengths = require_known_target(targets, "chain-id", name)
        if not isinstance(assignment, list) or len(assignment) != 2:
            raise ValidationError(f"chain-id:{name}: value must be [designed_chains, fixed_chains]")
        seen: set[str] = set()
        for group_name, group in zip(("designed", "fixed"), assignment):
            if not isinstance(group, list):
                raise ValidationError(f"chain-id:{name}: {group_name} chains must be a list")
            for chain in group:
                check_chain(lengths, "chain-id", name, chain)
                if chain in seen:
                    raise ValidationError(f"chain-id:{name}: chain {chain!r} appears more than once")
                seen.add(chain)
        if lengths and seen != set(lengths):
            missing = sorted(set(lengths) - seen)
            extra = sorted(seen - set(lengths))
            if missing:
                print(f"warning: chain-id:{name}: parsed chains not assigned: {missing}", file=sys.stderr)
            if extra:
                raise ValidationError(f"chain-id:{name}: unknown chains assigned: {extra}")


def validate_fixed_positions(data: dict[str, Any] | None, targets: dict[str, dict[str, Any]]) -> None:
    if data is None:
        return
    for name, chain_map in data.items():
        lengths = require_known_target(targets, "fixed-positions", name)
        if not isinstance(chain_map, dict):
            raise ValidationError(f"fixed-positions:{name}: target value must be a chain object")
        for chain, positions in chain_map.items():
            length = check_chain(lengths, "fixed-positions", name, chain)
            check_positions(positions, length, f"fixed-positions:{name}:{chain}")


def validate_tied_positions(data: dict[str, Any] | None, targets: dict[str, dict[str, Any]]) -> None:
    if data is None:
        return
    for name, groups in data.items():
        lengths = require_known_target(targets, "tied-positions", name)
        if not isinstance(groups, list):
            raise ValidationError(f"tied-positions:{name}: value must be a list of tie groups")
        for group_index, group in enumerate(groups, start=1):
            if not isinstance(group, dict):
                raise ValidationError(f"tied-positions:{name}: group {group_index} must be an object")
            if len(group) < 2:
                print(f"warning: tied-positions:{name}: group {group_index} ties fewer than two chains", file=sys.stderr)
            for chain, value in group.items():
                length = check_chain(lengths, "tied-positions", name, chain)
                context = f"tied-positions:{name}:group{group_index}:{chain}"
                if isinstance(value, list) and len(value) == 2 and all(isinstance(part, list) for part in value) and any(is_number(x) for x in value[1]):
                    positions, betas = value
                    check_positions(positions, length, context)
                    if len(positions) != len(betas):
                        raise ValidationError(f"{context}: weighted positions and betas must have equal length")
                    for beta in betas:
                        if not is_number(beta):
                            raise ValidationError(f"{context}: beta {beta!r} is not numeric")
                else:
                    check_positions(value, length, context)


def validate_bias_aa(data: dict[str, Any] | None) -> None:
    if data is None:
        return
    for amino_acid, bias in data.items():
        if not isinstance(amino_acid, str) or amino_acid not in ALPHABET or len(amino_acid) != 1:
            raise ValidationError(f"bias-aa: invalid amino acid key {amino_acid!r}; expected one of {ALPHABET}")
        if not is_number(bias):
            raise ValidationError(f"bias-aa:{amino_acid}: bias must be numeric")


def validate_bias_by_res(data: dict[str, Any] | None, targets: dict[str, dict[str, Any]]) -> None:
    if data is None:
        return
    for name, chain_map in data.items():
        lengths = require_known_target(targets, "bias-by-res", name)
        if not isinstance(chain_map, dict):
            raise ValidationError(f"bias-by-res:{name}: target value must be a chain object")
        for chain, matrix in chain_map.items():
            length = check_chain(lengths, "bias-by-res", name, chain)
            check_matrix(matrix, length, 21, f"bias-by-res:{name}:{chain}")


def validate_omit_aa(data: dict[str, Any] | None, targets: dict[str, dict[str, Any]]) -> None:
    if data is None:
        return
    for name, chain_map in data.items():
        lengths = require_known_target(targets, "omit-aa", name)
        if not isinstance(chain_map, dict):
            raise ValidationError(f"omit-aa:{name}: target value must be a chain object")
        for chain, entries in chain_map.items():
            length = check_chain(lengths, "omit-aa", name, chain)
            if not isinstance(entries, list):
                raise ValidationError(f"omit-aa:{name}:{chain}: value must be a list")
            for entry_index, entry in enumerate(entries, start=1):
                if not isinstance(entry, list) or len(entry) != 2:
                    raise ValidationError(f"omit-aa:{name}:{chain}: entry {entry_index} must be [position, omit_string]")
                position, omit_string = entry
                check_positions([position], length, f"omit-aa:{name}:{chain}:entry{entry_index}")
                if not isinstance(omit_string, str) or not omit_string:
                    raise ValidationError(f"omit-aa:{name}:{chain}: entry {entry_index} omit string must be non-empty")
                invalid = sorted(set(omit_string) - set(ALPHABET))
                if invalid:
                    raise ValidationError(f"omit-aa:{name}:{chain}: entry {entry_index} invalid amino acids {invalid}")


def validate_pssm(data: dict[str, Any] | None, targets: dict[str, dict[str, Any]]) -> None:
    if data is None:
        return
    for name, chain_map in data.items():
        lengths = require_known_target(targets, "pssm", name)
        if not isinstance(chain_map, dict):
            raise ValidationError(f"pssm:{name}: target value must be a chain object")
        for chain, pssm in chain_map.items():
            length = check_chain(lengths, "pssm", name, chain)
            if not isinstance(pssm, dict):
                raise ValidationError(f"pssm:{name}:{chain}: value must be an object")
            for key in ("pssm_coef", "pssm_bias", "pssm_log_odds"):
                if key not in pssm:
                    raise ValidationError(f"pssm:{name}:{chain}: missing {key}")
            coef = pssm["pssm_coef"]
            if not isinstance(coef, list):
                raise ValidationError(f"pssm:{name}:{chain}: pssm_coef must be a list")
            if length is not None and len(coef) != length:
                raise ValidationError(f"pssm:{name}:{chain}: pssm_coef length {len(coef)} != parsed chain length {length}")
            for index, value in enumerate(coef, start=1):
                if not is_number(value):
                    raise ValidationError(f"pssm:{name}:{chain}: pssm_coef[{index}] is not numeric")
                if float(value) < 0.0 or float(value) > 1.0:
                    print(f"warning: pssm:{name}:{chain}: pssm_coef[{index}]={value} is outside [0, 1]", file=sys.stderr)
            check_matrix(pssm["pssm_bias"], length, 21, f"pssm:{name}:{chain}:pssm_bias", probability_like=True)
            check_matrix(pssm["pssm_log_odds"], length, 21, f"pssm:{name}:{chain}:pssm_log_odds")


def validate_homooligomer_lengths(targets: dict[str, dict[str, Any]]) -> None:
    if not targets:
        raise ValidationError("--require-homooligomer-equal-length requires --parsed")
    for name, target in targets.items():
        lengths = chain_lengths(target)
        unique_lengths = sorted(set(lengths.values()))
        if len(unique_lengths) > 1:
            raise ValidationError(f"homooligomer:{name}: chain lengths differ: {lengths}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parsed", help="parsed PDB JSONL from parse_multiple_chains.py")
    parser.add_argument("--chain-id", help="chain assignment JSONL for --chain_id_jsonl")
    parser.add_argument("--fixed-positions", help="fixed positions JSONL for --fixed_positions_jsonl")
    parser.add_argument("--tied-positions", help="tied positions JSONL for --tied_positions_jsonl")
    parser.add_argument("--bias-aa", help="global amino-acid bias JSONL for --bias_AA_jsonl")
    parser.add_argument("--bias-by-res", help="per-residue bias JSONL for --bias_by_res_jsonl")
    parser.add_argument("--omit-aa", help="per-residue omit-AA JSONL for --omit_AA_jsonl")
    parser.add_argument("--pssm", help="PSSM JSONL for --pssm_jsonl")
    parser.add_argument("--require-homooligomer-equal-length", action="store_true", help="fail if parsed target chains have unequal lengths")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        targets = parsed_targets(args.parsed)
        validate_chain_id(load_single_dict(args.chain_id, "chain-id"), targets)
        validate_fixed_positions(load_single_dict(args.fixed_positions, "fixed-positions"), targets)
        validate_tied_positions(load_single_dict(args.tied_positions, "tied-positions"), targets)
        validate_bias_aa(load_single_dict(args.bias_aa, "bias-aa"))
        validate_bias_by_res(load_single_dict(args.bias_by_res, "bias-by-res"), targets)
        validate_omit_aa(load_single_dict(args.omit_aa, "omit-aa"), targets)
        validate_pssm(load_single_dict(args.pssm, "pssm"), targets)
        if args.require_homooligomer_equal_length:
            validate_homooligomer_lengths(targets)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("OK: constraint JSONL validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
