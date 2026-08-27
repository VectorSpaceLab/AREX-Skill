#!/usr/bin/env python3
"""Convert validated JSONL rows into a SaProt-style LMDB split."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

GB = 1024 ** 3
DEFAULT_MAP_SIZE_GB = 10 * 1024

BASE_FIELDS: Mapping[str, Sequence[str]] = {
    "any": (),
    "classification": ("seq", "label"),
    "regression": ("seq", "fitness"),
    "lm": ("seq",),
    "foldseek": ("seq",),
    "ppi": ("seq_1", "seq_2", "label"),
    "contact": ("seq", "valid_mask", "tertiary"),
}

PLDDT_FIELDS: Mapping[str, Sequence[str]] = {
    "classification": ("plddt",),
    "regression": ("plddt",),
    "ppi": ("plddt_1", "plddt_2"),
}

BIAS_FIELDS: Mapping[str, Sequence[str]] = {
    "classification": ("coords",),
    "lm": ("coords",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate JSONL rows and write a SaProt-style LMDB with info, length, and numeric keys."
    )
    parser.add_argument("--jsonl", required=True, type=Path, help="Input JSONL file containing one JSON object per line.")
    parser.add_argument("--lmdb-dir", required=True, type=Path, help="Output LMDB directory for one split.")
    parser.add_argument(
        "--dataset-type",
        choices=sorted(BASE_FIELDS),
        default="any",
        help="Validate rows for a known SaProt dataset schema before writing.",
    )
    parser.add_argument(
        "--require-plddt",
        action="store_true",
        help="Require pLDDT fields used when dataset kwargs include plddt_threshold.",
    )
    parser.add_argument(
        "--require-coords",
        action="store_true",
        help="Require coords fields used when dataset kwargs include use_bias_feature.",
    )
    parser.add_argument(
        "--map-size-gb",
        type=float,
        default=DEFAULT_MAP_SIZE_GB,
        help="LMDB map size in GiB. SaProt's source helper uses 10240 GiB by default.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Remove an existing non-empty LMDB directory before writing.")
    parser.add_argument("--dry-run", action="store_true", help="Validate JSONL rows without writing LMDB output.")
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def is_non_string_sequence(value: Any) -> bool:
    return isinstance(value, list) or isinstance(value, tuple)


def require_fields(row: Mapping[str, Any], fields: Iterable[str], line_no: int) -> None:
    missing = [field for field in fields if field not in row]
    if missing:
        fail(f"line {line_no}: missing required field(s): {', '.join(missing)}")


def sequence_token_count(seq: Any) -> int | None:
    if not isinstance(seq, str):
        return None
    if " " in seq.strip():
        return len([token for token in seq.split(" ") if token])
    if len(seq) % 2 == 0:
        return len(seq) // 2
    return len(seq)


def validate_plddt(row: Mapping[str, Any], seq_key: str, plddt_key: str, line_no: int) -> None:
    plddt = row.get(plddt_key)
    if not is_non_string_sequence(plddt):
        fail(f"line {line_no}: {plddt_key} must be a list when pLDDT validation is requested")
    token_count = sequence_token_count(row.get(seq_key))
    if token_count is not None and len(plddt) not in {token_count, len(str(row.get(seq_key, "")))}:
        fail(
            f"line {line_no}: {plddt_key} length {len(plddt)} does not match inferred token count "
            f"{token_count} for {seq_key}"
        )


def validate_coords(row: Mapping[str, Any], line_no: int) -> None:
    coords = row.get("coords")
    if not isinstance(coords, dict) or not coords:
        fail(f"line {line_no}: coords must be a non-empty object when coordinate validation is requested")
    for atom_name, values in coords.items():
        if not is_non_string_sequence(values):
            fail(f"line {line_no}: coords.{atom_name} must be a list of coordinates")


def validate_contact(row: Mapping[str, Any], line_no: int) -> None:
    valid_mask = row.get("valid_mask")
    tertiary = row.get("tertiary")
    if not is_non_string_sequence(valid_mask):
        fail(f"line {line_no}: valid_mask must be a list")
    if not is_non_string_sequence(tertiary):
        fail(f"line {line_no}: tertiary must be a list of 3D coordinates")
    if len(valid_mask) != len(tertiary):
        fail(f"line {line_no}: valid_mask length {len(valid_mask)} does not match tertiary length {len(tertiary)}")
    for index, coord in enumerate(tertiary[:5]):
        if not is_non_string_sequence(coord) or len(coord) != 3:
            fail(f"line {line_no}: tertiary[{index}] must contain three numeric coordinates")


def validate_row(row: Mapping[str, Any], dataset_type: str, require_plddt: bool, require_coords: bool, line_no: int) -> None:
    require_fields(row, BASE_FIELDS[dataset_type], line_no)

    if "seq" in row and not isinstance(row["seq"], str):
        fail(f"line {line_no}: seq must be a string")
    if "seq_1" in row and not isinstance(row["seq_1"], str):
        fail(f"line {line_no}: seq_1 must be a string")
    if "seq_2" in row and not isinstance(row["seq_2"], str):
        fail(f"line {line_no}: seq_2 must be a string")
    if "fitness" in row and not isinstance(row["fitness"], (int, float)):
        fail(f"line {line_no}: fitness must be numeric")

    if require_plddt:
        require_fields(row, PLDDT_FIELDS.get(dataset_type, ()), line_no)
        if dataset_type in {"classification", "regression"}:
            validate_plddt(row, "seq", "plddt", line_no)
        elif dataset_type == "ppi":
            validate_plddt(row, "seq_1", "plddt_1", line_no)
            validate_plddt(row, "seq_2", "plddt_2", line_no)

    if require_coords:
        require_fields(row, BIAS_FIELDS.get(dataset_type, ()), line_no)
        if "coords" in row:
            validate_coords(row, line_no)

    if dataset_type == "contact":
        validate_contact(row, line_no)


def read_validated_rows(path: Path, dataset_type: str, require_plddt: bool, require_coords: bool) -> List[str]:
    if not path.is_file():
        fail(f"JSONL input does not exist or is not a file: {path}")

    rows: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                fail(f"line {line_no}: blank lines are not valid SaProt JSONL rows")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(f"line {line_no}: invalid JSON: {exc}")
            if not isinstance(row, dict):
                fail(f"line {line_no}: row must be a JSON object")
            validate_row(row, dataset_type, require_plddt, require_coords, line_no)
            rows.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))

    if not rows:
        fail("JSONL input contains no rows")
    return rows


def prepare_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not overwrite:
            fail(f"output directory is not empty: {path}. Use --overwrite to replace it.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def load_lmdb_module():
    try:
        import lmdb  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on host environment
        raise SystemExit(
            "ERROR: Missing dependency 'lmdb'. Install it in the active Python environment "
            "before writing or verifying an LMDB."
        ) from exc
    return lmdb


def write_lmdb(rows: Sequence[str], lmdb_dir: Path, map_size_gb: float) -> None:
    if map_size_gb <= 0:
        fail("--map-size-gb must be positive")
    lmdb = load_lmdb_module()
    map_size = int(map_size_gb * GB)
    env = lmdb.open(str(lmdb_dir), map_size=map_size)
    try:
        with env.begin(write=True) as txn:
            for index, row in enumerate(rows):
                txn.put(str(index).encode("utf-8"), row.encode("utf-8"))
            info = (
                "Keys are as follows:\n"
                "\tinfo: description of dataset\n"
                "\tlength: length of data\n"
                "\t0 ~ length-1: index of each data\n"
            )
            txn.put(b"info", info.encode("utf-8"))
            txn.put(b"length", str(len(rows)).encode("utf-8"))
    finally:
        env.close()


def verify_lmdb(lmdb_dir: Path, expected_length: int) -> None:
    lmdb = load_lmdb_module()
    env = lmdb.open(str(lmdb_dir), readonly=True, lock=False, max_readers=1)
    try:
        with env.begin() as txn:
            raw_length = txn.get(b"length")
            if raw_length is None:
                fail("wrote LMDB but length key is missing")
            actual_length = int(raw_length.decode("utf-8"))
            if actual_length != expected_length:
                fail(f"wrote LMDB length {actual_length}, expected {expected_length}")
            for key in (b"info", b"0", str(expected_length - 1).encode("utf-8")):
                if txn.get(key) is None:
                    fail(f"wrote LMDB but key {key.decode('utf-8')} is missing")
    finally:
        env.close()


def main() -> int:
    args = parse_args()
    rows = read_validated_rows(args.jsonl, args.dataset_type, args.require_plddt, args.require_coords)
    if args.dry_run:
        print(f"Validated {len(rows)} JSONL row(s); no LMDB written.")
        return 0

    prepare_output_dir(args.lmdb_dir, args.overwrite)
    write_lmdb(rows, args.lmdb_dir, args.map_size_gb)
    verify_lmdb(args.lmdb_dir, len(rows))
    print(f"Wrote {len(rows)} row(s) to {args.lmdb_dir}")
    print("Created keys: info, length, and numeric row keys 0..length-1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
