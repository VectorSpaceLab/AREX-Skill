#!/usr/bin/env python3
"""Update SchNetPack ASE DB unit metadata.

This helper is self-contained for generated SchNetPack skills. It updates the
ASE database metadata expected by SchNetPack 2.x and can migrate legacy atomref
metadata produced by older SchNetPack datasets.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Dict, Iterable, List


ANGSTROM_ALIASES = {"ang", "angstrom"}


def parse_property_units(value: str | None) -> Dict[str, str]:
    if value is None or value == "":
        return {}

    parsed: Dict[str, str] = {}
    pairs = [item.strip() for item in value.split(",") if item.strip()]
    if not pairs:
        raise argparse.ArgumentTypeError(
            "--propunit must contain at least one property:unit pair."
        )

    for pair in pairs:
        if ":" not in pair:
            raise argparse.ArgumentTypeError(
                f"Invalid property unit pair {pair!r}; expected PROPERTY:UNIT."
            )
        prop, unit = [part.strip() for part in pair.split(":", 1)]
        if not prop:
            raise argparse.ArgumentTypeError(
                f"Invalid property unit pair {pair!r}; property name is empty."
            )
        if not unit:
            raise argparse.ArgumentTypeError(
                f"Invalid property unit pair {pair!r}; unit string is empty."
            )
        if prop in parsed:
            raise argparse.ArgumentTypeError(
                f"Duplicate property {prop!r} in --propunit."
            )
        parsed[prop] = unit
    return parsed


def validate_distance_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    unit = unit.strip()
    if not unit:
        raise argparse.ArgumentTypeError("--distunit cannot be empty.")
    if unit == "A":
        raise argparse.ArgumentTypeError(
            "Distance unit 'A' is Ampere in ASE unit definitions. Use 'Ang' or "
            "'Angstrom' for Angstrom distances, and also check property units such "
            "as forces."
        )
    if unit.lower() in ANGSTROM_ALIASES and unit != "Ang":
        print(
            f"warning: distance unit {unit!r} is accepted, but SchNetPack examples "
            "usually use 'Ang'.",
            file=sys.stderr,
        )
    return unit


def migrate_atomrefs(metadata: dict, quiet: bool = False) -> dict:
    import numpy as np

    metadata = copy.deepcopy(metadata)

    if "atomrefs" not in metadata:
        metadata["atomrefs"] = {}
        return metadata

    if "atref_labels" not in metadata:
        return metadata

    old_atomrefs = np.array(metadata["atomrefs"])
    labels = metadata["atref_labels"]
    if isinstance(labels, str):
        labels = [labels]

    if old_atomrefs.ndim == 1:
        old_atomrefs = old_atomrefs[:, None]
    if old_atomrefs.ndim != 2:
        raise ValueError(
            "Legacy atomrefs must be a one- or two-dimensional array when "
            "atref_labels are present."
        )
    if old_atomrefs.shape[1] < len(labels):
        raise ValueError(
            "Legacy atomrefs has fewer columns than atref_labels entries: "
            f"shape={old_atomrefs.shape}, labels={labels!r}."
        )

    new_atomrefs = {}
    for index, label in enumerate(labels):
        if not quiet:
            print(f"migrate atomrefs column {index} -> {label}")
        new_atomrefs[str(label)] = old_atomrefs[:, index].tolist()

    metadata["atomrefs"] = new_atomrefs
    del metadata["atref_labels"]
    return metadata


def update_metadata(
    data_path: Path,
    distance_unit: str | None,
    property_units: Dict[str, str],
    dry_run: bool,
    quiet: bool,
) -> None:
    from ase.db import connect

    with connect(str(data_path)) as db:
        metadata = copy.deepcopy(db.metadata)

    if not quiet:
        print("current metadata:")
        print(metadata)

    metadata = migrate_atomrefs(metadata, quiet=quiet)

    if distance_unit is not None:
        metadata["_distance_unit"] = distance_unit

    if property_units:
        metadata.setdefault("_property_unit_dict", {})
        if not isinstance(metadata["_property_unit_dict"], dict):
            raise ValueError("Existing _property_unit_dict metadata is not a dict.")
        metadata["_property_unit_dict"].update(property_units)

    if not quiet:
        print("updated metadata:")
        print(metadata)

    if dry_run:
        print("dry-run: metadata was not written")
        return

    with connect(str(data_path)) as db:
        db.metadata = metadata


def expand_property_dims(
    data_path: Path,
    properties: Iterable[str],
    dry_run: bool,
    quiet: bool,
) -> None:
    import numpy as np
    from ase.db import connect
    from tqdm import tqdm

    properties = list(properties)
    if not properties:
        return

    with connect(str(data_path)) as db:
        total = len(db)
        iterator = range(total)
        if not quiet:
            iterator = tqdm(iterator, desc="expanding properties")
        for index in iterator:
            row = db.get(index + 1)
            data = {}
            changed = False
            missing = []
            for prop in properties:
                if prop not in row.data:
                    missing.append(prop)
                    continue
                data[prop] = np.expand_dims(row.data[prop], 0)
                changed = True

            if missing and not quiet:
                print(
                    f"warning: row {index + 1} is missing properties: "
                    + ", ".join(missing),
                    file=sys.stderr,
                )
            if changed and not dry_run:
                db.update(index + 1, data=data)

    if dry_run:
        print("dry-run: property dimensions were not written")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Set or repair SchNetPack ASE DB unit metadata. This is useful for "
            "legacy ASE databases that lack _distance_unit, _property_unit_dict, "
            "or SchNetPack 2.x atomrefs metadata."
        )
    )
    parser.add_argument("data_path", help="Path to the ASE DB dataset to update.")
    parser.add_argument(
        "--distunit",
        type=validate_distance_unit,
        help="Distance unit string for positions/cell, e.g. 'Ang'. Do not use 'A'.",
    )
    parser.add_argument(
        "--propunit",
        type=parse_property_units,
        default={},
        help=(
            "Property units as comma-separated PROPERTY:UNIT pairs, e.g. "
            "'energy:eV,forces:eV/Ang'."
        ),
    )
    parser.add_argument(
        "--expand-property-dims",
        "--expand_property_dims",
        nargs="+",
        default=[],
        metavar="PROPERTY",
        help=(
            "Expand the first dimension of selected row data properties. This can "
            "repair some older datasets whose scalar/vector properties lack a "
            "leading dimension."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned metadata changes and skip writes.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress metadata/progress output except warnings and errors.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data_path = Path(args.data_path).expanduser()
    if not data_path.exists():
        parser.error(f"ASE DB does not exist: {data_path}")
    if data_path.suffix != ".db":
        parser.error(
            f"Expected an ASE DB file with '.db' suffix, got: {data_path.name!r}"
        )

    try:
        update_metadata(
            data_path=data_path,
            distance_unit=args.distunit,
            property_units=args.propunit,
            dry_run=args.dry_run,
            quiet=args.quiet,
        )
        expand_property_dims(
            data_path=data_path,
            properties=args.expand_property_dims,
            dry_run=args.dry_run,
            quiet=args.quiet,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
