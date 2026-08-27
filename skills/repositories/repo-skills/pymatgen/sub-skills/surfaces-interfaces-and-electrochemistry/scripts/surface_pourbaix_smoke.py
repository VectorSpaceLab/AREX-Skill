#!/usr/bin/env python3
"""Smoke-check pymatgen surface, interface, and Pourbaix analysis APIs.

The check uses only tiny in-memory objects. It performs no network access, reads
no fixtures, and delays pymatgen imports until after argparse so --help works in
plain Python environments.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe in-memory smoke checks for WulffShape, ZSLGenerator, "
            "PourbaixEntry, and optional InterfacialReactivity."
        )
    )
    parser.add_argument(
        "--skip-interface-reactivity",
        action="store_true",
        help="Skip the tiny PhaseDiagram/InterfacialReactivity calculation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a compact JSON summary instead of human-readable lines.",
    )
    return parser.parse_args()


def run_smoke(skip_interface_reactivity: bool) -> dict[str, Any]:
    import numpy as np

    from pymatgen.analysis.interfaces.zsl import ZSLGenerator
    from pymatgen.analysis.pourbaix_diagram import PourbaixEntry
    from pymatgen.analysis.wulff import WulffShape
    from pymatgen.core import Composition, Lattice
    from pymatgen.entries.computed_entries import ComputedEntry

    results: dict[str, Any] = {}

    wulff = WulffShape(Lattice.cubic(1.0), [(1, 0, 0)], [1.0])
    results["wulff_area_fraction_100"] = float(wulff.area_fraction_dict[(1, 0, 0)])
    results["wulff_weighted_surface_energy"] = float(wulff.weighted_surface_energy)

    vectors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    zsl_matches = list(ZSLGenerator(max_area=4)(vectors, vectors, lowest=True))
    if not zsl_matches:
        raise RuntimeError("Expected at least one ZSL match for identical square surface lattices.")
    results["zsl_first_match_area"] = float(zsl_matches[0].match_area)

    pourbaix_entry = PourbaixEntry(ComputedEntry("ZnO", -3.0), entry_id="toy-zno")
    results["pourbaix_phase_type"] = pourbaix_entry.phase_type
    results["pourbaix_energy_at_ph7_v0"] = float(pourbaix_entry.energy_at_conditions(pH=7.0, V=0.0))

    if not skip_interface_reactivity:
        from pymatgen.analysis.interface_reactions import InterfacialReactivity
        from pymatgen.analysis.phase_diagram import PhaseDiagram

        entries = [
            ComputedEntry("Li", 0.0),
            ComputedEntry("O2", 0.0),
            ComputedEntry("Li2O", -6.0),
        ]
        phase_diagram = PhaseDiagram(entries)
        reactivity = InterfacialReactivity(
            Composition("Li"),
            Composition("Li2O"),
            phase_diagram,
            use_hull_energy=True,
        )
        results["interfacial_kink_count"] = len(reactivity.get_kinks())

    return results


def main() -> int:
    args = parse_args()
    try:
        results = run_smoke(skip_interface_reactivity=args.skip_interface_reactivity)
    except ModuleNotFoundError as exc:
        print(
            f"Missing dependency while importing pymatgen analysis APIs: {exc}. "
            "Run this script in an environment with pymatgen installed.",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:
        print(f"Smoke check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, sort_keys=True))
    else:
        for key, value in sorted(results.items()):
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
