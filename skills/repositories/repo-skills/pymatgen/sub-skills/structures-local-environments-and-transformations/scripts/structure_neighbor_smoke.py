#!/usr/bin/env python3
"""Safe in-memory smoke checks for pymatgen structure/local-environment workflows."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build tiny in-memory pymatgen structures and print deterministic "
            "neighbor, dimensionality, and matcher diagnostics."
        )
    )
    parser.add_argument(
        "--case",
        choices=("neighbors", "compare", "matcher"),
        default="neighbors",
        help="Smoke case to run: one strategy, strategy comparison, or StructureMatcher comparator mismatch.",
    )
    parser.add_argument(
        "--strategy",
        choices=("auto", "crystalnn", "minimum-distance", "voronoi"),
        default="auto",
        help="Neighbor strategy for --case neighbors. 'auto' tries CrystalNN and falls back to MinimumDistanceNN.",
    )
    parser.add_argument(
        "--site-index",
        type=int,
        default=0,
        help="Site index to analyze in the in-memory CsCl structure.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text summary.",
    )
    return parser


def _make_cscl(with_oxidation: bool = True):
    from pymatgen.core import Lattice, Structure

    species = ["Cs+", "Cl-"] if with_oxidation else ["Cs", "Cl"]
    return Structure(
        Lattice.cubic(4.12),
        species,
        [[0, 0, 0], [0.5, 0.5, 0.5]],
    )


def _make_strategy(name: str):
    from pymatgen.analysis.local_env import CrystalNN, MinimumDistanceNN, VoronoiNN

    if name == "crystalnn":
        return "CrystalNN", CrystalNN(search_cutoff=6)
    if name == "minimum-distance":
        return "MinimumDistanceNN", MinimumDistanceNN(cutoff=6)
    if name == "voronoi":
        return "VoronoiNN", VoronoiNN(cutoff=6)
    raise ValueError(f"unknown strategy: {name}")


def _auto_strategy():
    try:
        return _make_strategy("crystalnn")
    except Exception as exc:
        sys.stderr.write(
            f"CrystalNN unavailable ({type(exc).__name__}: {exc}); falling back to MinimumDistanceNN.\n"
        )
        return _make_strategy("minimum-distance")


def _normalize_image(image: Any) -> tuple[int | float | str, ...] | None:
    if image is None:
        return None
    normalized = []
    for value in image:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            normalized.append(str(value))
            continue
        rounded = round(numeric)
        normalized.append(int(rounded) if math.isclose(numeric, rounded, abs_tol=1e-8) else round(numeric, 8))
    return tuple(normalized)


def _neighbor_rows(structure, site_index: int, info: list[dict[str, Any]]) -> list[dict[str, Any]]:
    center = structure[site_index]
    rows = []
    for item in info:
        site = item["site"]
        rows.append(
            {
                "species": site.species_string,
                "distance": round(float(center.distance(site)), 6),
                "image": _normalize_image(item.get("image")),
                "weight": round(float(item.get("weight", 1.0)), 6),
            }
        )
    return sorted(rows, key=lambda row: (row["distance"], row["species"], str(row["image"]), row["weight"]))


def _summarize_neighbors(args: argparse.Namespace) -> dict[str, Any]:
    from pymatgen.analysis.dimensionality import get_dimensionality_larsen, get_structure_components

    structure = _make_cscl(with_oxidation=True)
    if args.site_index < 0 or args.site_index >= len(structure):
        raise ValueError(f"site index {args.site_index} is outside 0..{len(structure) - 1}")

    strategy_label, strategy = _auto_strategy() if args.strategy == "auto" else _make_strategy(args.strategy)
    info = strategy.get_nn_info(structure, args.site_index)
    rows = _neighbor_rows(structure, args.site_index, info)
    species_counts = dict(sorted(Counter(row["species"] for row in rows).items()))

    bonded = strategy.get_bonded_structure(structure)
    components = get_structure_components(bonded, inc_orientation=True, inc_site_ids=True)
    dimensionalities = sorted(int(component["dimensionality"]) for component in components)

    return {
        "case": "neighbors",
        "formula": structure.formula,
        "reduced_formula": structure.composition.reduced_formula,
        "strategy": strategy_label,
        "site_index": args.site_index,
        "site_species": structure[args.site_index].species_string,
        "coordination_number": float(strategy.get_cn(structure, args.site_index)),
        "neighbor_count": len(rows),
        "neighbor_species_counts": species_counts,
        "neighbors": rows,
        "dimensionality_larsen": int(get_dimensionality_larsen(bonded)),
        "component_dimensionalities": dimensionalities,
    }


def _summarize_compare(args: argparse.Namespace) -> dict[str, Any]:
    structure = _make_cscl(with_oxidation=True)
    if args.site_index < 0 or args.site_index >= len(structure):
        raise ValueError(f"site index {args.site_index} is outside 0..{len(structure) - 1}")

    strategy_names = ("crystalnn", "minimum-distance", "voronoi")
    results = []
    for name in strategy_names:
        label, strategy = _make_strategy(name)
        info = strategy.get_nn_info(structure, args.site_index)
        rows = _neighbor_rows(structure, args.site_index, info)
        results.append(
            {
                "strategy": label,
                "coordination_number": float(strategy.get_cn(structure, args.site_index)),
                "neighbor_count": len(rows),
                "neighbor_species_counts": dict(sorted(Counter(row["species"] for row in rows).items())),
                "first_neighbors": rows[:8],
            }
        )

    return {
        "case": "compare",
        "formula": structure.formula,
        "site_index": args.site_index,
        "site_species": structure[args.site_index].species_string,
        "results": results,
        "interpretation_hint": (
            "Disagreement is expected when raw Voronoi contacts, distance shells, and CrystalNN heuristics are compared."
        ),
    }


def _summarize_matcher() -> dict[str, Any]:
    from pymatgen.analysis.structure_matcher import ElementComparator, SpeciesComparator, StructureMatcher

    with_oxidation = _make_cscl(with_oxidation=True)
    neutral = _make_cscl(with_oxidation=False)
    strict = StructureMatcher(comparator=SpeciesComparator())
    by_element = StructureMatcher(comparator=ElementComparator())

    return {
        "case": "matcher",
        "structure_1_species": [site.species_string for site in with_oxidation],
        "structure_2_species": [site.species_string for site in neutral],
        "species_comparator_match": bool(strict.fit(with_oxidation, neutral)),
        "element_comparator_match": bool(by_element.fit(with_oxidation, neutral)),
        "diagnosis": "SpeciesComparator treats oxidation-state-decorated species differently; ElementComparator ignores oxidation states.",
    }


def _print_neighbors(summary: dict[str, Any]) -> None:
    print("pymatgen structure-neighbor smoke")
    print(f"formula: {summary['formula']} (reduced={summary['reduced_formula']})")
    print(f"strategy: {summary['strategy']}")
    print(
        f"site {summary['site_index']}: {summary['site_species']} "
        f"cn={summary['coordination_number']:.6g} neighbors={summary['neighbor_count']}"
    )
    print(f"neighbor species counts: {summary['neighbor_species_counts']}")
    print(f"dimensionality_larsen: {summary['dimensionality_larsen']}")
    print(f"component dimensionalities: {summary['component_dimensionalities']}")
    print("neighbors:")
    for row in summary["neighbors"]:
        print(
            "  "
            f"{row['species']:>4} distance={row['distance']:.6f} "
            f"image={row['image']} weight={row['weight']:.6g}"
        )


def _print_compare(summary: dict[str, Any]) -> None:
    print("pymatgen neighbor-strategy comparison")
    print(f"formula: {summary['formula']}")
    print(f"site {summary['site_index']}: {summary['site_species']}")
    for result in summary["results"]:
        print(
            f"{result['strategy']}: cn={result['coordination_number']:.6g} "
            f"neighbors={result['neighbor_count']} species={result['neighbor_species_counts']}"
        )
    print(summary["interpretation_hint"])


def _print_matcher(summary: dict[str, Any]) -> None:
    print("pymatgen StructureMatcher comparator smoke")
    print(f"structure 1 species: {summary['structure_1_species']}")
    print(f"structure 2 species: {summary['structure_2_species']}")
    print(f"SpeciesComparator match: {summary['species_comparator_match']}")
    print(f"ElementComparator match: {summary['element_comparator_match']}")
    print(summary["diagnosis"])


def _print_text(summary: dict[str, Any]) -> None:
    if summary["case"] == "neighbors":
        _print_neighbors(summary)
    elif summary["case"] == "compare":
        _print_compare(summary)
    elif summary["case"] == "matcher":
        _print_matcher(summary)
    else:
        raise ValueError(f"unknown case: {summary['case']}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.case == "neighbors":
            summary = _summarize_neighbors(args)
        elif args.case == "compare":
            summary = _summarize_compare(args)
        else:
            summary = _summarize_matcher()
    except Exception as exc:
        sys.stderr.write(f"ERROR: {type(exc).__name__}: {exc}\n")
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        _print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
