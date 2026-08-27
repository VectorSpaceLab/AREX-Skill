#!/usr/bin/env python3
"""Safe in-memory smoke check for pymatgen entries, compatibility, batteries, and Borg imports.

The script intentionally avoids network access, user calculation directories,
fixtures, downloads, GUI use, and destructive writes. It constructs tiny objects
only to verify import/API readiness and to surface expected diagnostics.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a safe in-memory smoke check for pymatgen entry/battery/Borg APIs.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the readiness report as JSON instead of human-readable lines.",
    )
    return parser


def run_smoke() -> dict[str, Any]:
    from pymatgen.apps.battery.analyzer import BatteryAnalyzer
    from pymatgen.apps.battery.insertion_battery import InsertionVoltagePair
    from pymatgen.apps.borg.hive import VaspToComputedEntryDrone
    from pymatgen.apps.borg.queen import BorgQueen
    from pymatgen.core import Lattice, Structure
    from pymatgen.core.entries import ComputedEntry
    from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
    from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme

    report: dict[str, Any] = {
        "imports_ok": True,
        "compatibility_instantiated": False,
        "mixing_instantiated": False,
        "borg_instantiated_without_scan": False,
        "unoxidized_structure_diagnostic": None,
        "oxidized_capacity_positive": False,
        "insertion_voltage_pair_ready": False,
        "underdetermined_case_reported": False,
    }

    compat = MaterialsProject2020Compatibility(check_potcar=False)
    report["compatibility_instantiated"] = compat is not None

    mixing = MaterialsProjectDFTMixingScheme(check_potcar=False)
    report["mixing_instantiated"] = mixing is not None

    drone = VaspToComputedEntryDrone(inc_structure=False)
    queen = BorgQueen(drone, rootpath=None, number_of_drones=1)
    report["borg_instantiated_without_scan"] = queen.get_data() == []

    structure = Structure(
        Lattice.orthorhombic(10.3, 6.0, 4.7),
        ["Li", "Fe", "P", "O", "O", "O", "O"],
        [
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.5],
            [0.25, 0.25, 0.25],
            [0.30, 0.30, 0.30],
            [0.70, 0.30, 0.30],
            [0.30, 0.70, 0.30],
            [0.30, 0.30, 0.70],
        ],
    )

    try:
        BatteryAnalyzer(structure, working_ion="Li")
    except ValueError as exc:
        report["unoxidized_structure_diagnostic"] = str(exc)

    oxidized = structure.copy()
    oxidized.add_oxidation_state_by_element({"Li": 1, "Fe": 2, "P": 5, "O": -2})
    analyzer = BatteryAnalyzer(oxidized, working_ion="Li")
    report["oxidized_capacity_positive"] = analyzer.get_max_capgrav(insert=False) > 0
    report["max_ion_removal"] = float(analyzer.max_ion_removal)

    li_entry = ComputedEntry("Li", -1.9)
    charged = ComputedEntry("TiO2", -20.0, data={"volume": 35.0})
    discharged = ComputedEntry("LiTiO2", -24.0, data={"volume": 38.0})
    pair = InsertionVoltagePair.from_entries(charged, discharged, li_entry)
    report["insertion_voltage_pair_ready"] = pair.framework_formula == "TiO2" and pair.voltage > 0
    report["toy_pair_voltage"] = float(pair.voltage)

    try:
        same_fraction = ComputedEntry("LiTiO2", -24.1, data={"volume": 38.5})
        InsertionVoltagePair.from_entries(discharged, same_fraction, li_entry)
    except ValueError as exc:
        report["underdetermined_case_reported"] = "same" in str(exc).lower() or "framework" in str(exc).lower()
        report["underdetermined_case_message"] = str(exc)

    report["notes"] = [
        "Toy entries demonstrate API readiness only; they are not a scientific voltage curve.",
        "Borg objects were instantiated with rootpath=None, so no filesystem scan was performed.",
    ]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = run_smoke()
    except Exception as exc:  # pragma: no cover - intended CLI diagnostic
        print(f"entry/battery smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("pymatgen entry/battery smoke readiness:")
        for key, value in report.items():
            if key == "notes":
                continue
            print(f"- {key}: {value}")
        for note in report["notes"]:
            print(f"- note: {note}")

    required = [
        "imports_ok",
        "compatibility_instantiated",
        "mixing_instantiated",
        "borg_instantiated_without_scan",
        "oxidized_capacity_positive",
        "insertion_voltage_pair_ready",
        "underdetermined_case_reported",
    ]
    return 0 if all(report.get(key) for key in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
