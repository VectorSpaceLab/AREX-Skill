#!/usr/bin/env python3
"""Validate an AlphaFold 3 input JSON with the installed parser."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def _chain_kind(chain: object) -> str:
    name = type(chain).__name__.lower()
    if "protein" in name:
        return "protein"
    if "rna" in name:
        return "rna"
    if "dna" in name:
        return "dna"
    if "ligand" in name:
        return "ligand"
    return type(chain).__name__


def _chain_id(chain: object) -> str:
    return str(getattr(chain, "id", "?"))


def _chain_length(chain: object) -> str:
    try:
        return str(len(chain))
    except TypeError:
        return "?"


def _raw_dialect_version(json_text: str) -> tuple[str, str]:
    try:
        raw = json.loads(json_text)
    except json.JSONDecodeError:
        return "<invalid-json>", "<invalid-json>"
    if isinstance(raw, list):
        return "alphafoldserver-list", "<per-job>"
    return str(raw.get("dialect", "<missing>")), str(raw.get("version", "<missing>"))


def validate(path: pathlib.Path) -> int:
    try:
        from alphafold3.common import folding_input
    except Exception as exc:  # pragma: no cover - depends on user env.
        print(
            "ERROR: Unable to import alphafold3.common.folding_input: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    try:
        json_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Unable to read {path}: {exc}", file=sys.stderr)
        return 2

    try:
        fold_input = folding_input.Input.from_json(json_text, json_path=path)
    except Exception as exc:
        print(
            "ERROR: AlphaFold 3 input validation failed: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    dialect, version = _raw_dialect_version(json_text)
    chains = list(getattr(fold_input, "chains", ()))
    counts: dict[str, int] = {}
    for chain in chains:
        kind = _chain_kind(chain)
        counts[kind] = counts.get(kind, 0) + 1

    print("OK: AlphaFold 3 input JSON is valid")
    print(f"path: {path}")
    print(f"dialect: {dialect}")
    print(f"version: {version}")
    print(f"name: {fold_input.name}")
    print(f"sanitised_name: {fold_input.sanitised_name()}")
    print("seeds: " + ",".join(str(seed) for seed in fold_input.rng_seeds))
    print(f"chains_total: {len(chains)}")
    if counts:
        print(
            "chains_by_type: "
            + ", ".join(f"{kind}={counts[kind]}" for kind in sorted(counts))
        )
    print("chains:")
    for chain in chains:
        print(f"  - {_chain_id(chain)}: {_chain_kind(chain)} length={_chain_length(chain)}")
    print(f"bonded_atom_pairs: {len(fold_input.bonded_atom_pairs or ())}")
    print(f"user_ccd: {'yes' if fold_input.user_ccd else 'no'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one native AlphaFold 3 input JSON file using "
            "alphafold3.common.folding_input.Input.from_json."
        )
    )
    parser.add_argument(
        "json_path",
        type=pathlib.Path,
        help="Path to one native alphafold3 dialect input JSON file.",
    )
    args = parser.parse_args(argv)
    return validate(args.json_path)


if __name__ == "__main__":
    raise SystemExit(main())
