#!/usr/bin/env python3
"""Build a deterministic, transport-free OpenMC XML model fixture.

The fixture uses only public Python APIs. It contains one material-filled
sphere cell inside an explicit universe, bounded geometry, fixed-source
settings, and both separate and combined XML input files. It never invokes
transport, the OpenMC executable, the native shared library, or a download.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


RADIUS = 0.5
EXPECTED_ROOTS = {
    "materials.xml": "materials",
    "geometry.xml": "geometry",
    "settings.xml": "settings",
    "model.xml": "model",
}


def _load_openmc():
    """Import OpenMC with an error that explains the required prerequisite."""
    try:
        import openmc
    except Exception as exc:  # import failures vary by missing dependency
        raise RuntimeError(
            "could not import OpenMC; run this helper with the prepared "
            "OpenMC Python environment (the native executable and cross "
            "sections are not required)"
        ) from exc
    return openmc


def build_model():
    """Return a small public-API model whose XML needs no nuclear data."""
    openmc = _load_openmc()
    openmc.reset_auto_ids()

    material = openmc.Material(material_id=1, name="fixture material")
    material.add_nuclide("H1", 1.0)
    material.set_density("g/cm3", 1.0)
    materials = openmc.Materials([material])

    sphere = openmc.Sphere(
        surface_id=1,
        r=RADIUS,
        boundary_type="vacuum",
        name="fixture sphere",
    )
    cell = openmc.Cell(
        cell_id=1,
        name="sphere cell",
        fill=material,
        region=-sphere,
    )
    universe = openmc.Universe(universe_id=1, cells=[cell])
    geometry = openmc.Geometry(universe)

    settings = openmc.Settings(run_mode="fixed source", batches=1, particles=1)
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((0.0, 0.0, 0.0)),
        angle=openmc.stats.Isotropic(),
        energy=openmc.stats.Discrete([1.0e6], [1.0]),
        particle="neutron",
    )

    return openmc.Model(
        geometry=geometry,
        materials=materials,
        settings=settings,
        description="Deterministic XML-only sphere fixture",
    )


def _parse_xml(path: Path, expected_root: str) -> ET.Element:
    """Parse one generated document and report malformed output clearly."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise RuntimeError(f"cannot parse generated XML {path}: {exc}") from exc
    if root.tag != expected_root:
        raise RuntimeError(
            f"generated XML {path} has root {root.tag!r}; "
            f"expected {expected_root!r}"
        )
    return root


def _validate_fixture(output_dir: Path) -> None:
    """Check XML roots, essential references, and public XML round trips."""
    roots = {
        filename: _parse_xml(output_dir / filename, expected)
        for filename, expected in EXPECTED_ROOTS.items()
    }

    materials_root = roots["materials.xml"]
    geometry_root = roots["geometry.xml"]
    settings_root = roots["settings.xml"]
    model_root = roots["model.xml"]

    material_nodes = materials_root.findall("material")
    cell_nodes = geometry_root.findall("cell")
    surface_nodes = geometry_root.findall("surface")
    if len(material_nodes) != 1:
        raise RuntimeError("materials.xml should contain exactly one material")
    if len(cell_nodes) != 1 or cell_nodes[0].get("material") != "1":
        raise RuntimeError("geometry.xml should contain one material-filled cell")
    if cell_nodes[0].get("universe") != "1":
        raise RuntimeError("geometry.xml is missing the explicit universe reference")
    if len(surface_nodes) != 1 or surface_nodes[0].get("type") != "sphere":
        raise RuntimeError("geometry.xml should contain one sphere surface")
    if settings_root.find("source") is None:
        raise RuntimeError("settings.xml should contain a fixed-source definition")
    if model_root.find("materials") is None or model_root.find("geometry") is None:
        raise RuntimeError("model.xml is missing its materials or geometry section")
    if model_root.find("settings") is None:
        raise RuntimeError("model.xml is missing its settings section")

    # Re-read separate documents using public APIs. This validates object
    # ownership and references without invoking the executable or native code.
    openmc = _load_openmc()
    openmc.reset_auto_ids()
    materials = openmc.Materials.from_xml(output_dir / "materials.xml")
    geometry = openmc.Geometry.from_xml(
        output_dir / "geometry.xml", materials=materials
    )
    settings = openmc.Settings.from_xml(output_dir / "settings.xml")

    if len(materials) != 1 or len(geometry.get_all_cells()) != 1:
        raise RuntimeError("separate XML round trip changed material or cell count")
    if not isinstance(geometry.root_universe, openmc.Universe):
        raise RuntimeError("separate XML round trip did not restore a universe")
    if len(geometry.get_all_universes()) != 1:
        raise RuntimeError("separate XML round trip changed universe count")
    if settings.run_mode != "fixed source" or settings.source is None:
        raise RuntimeError("separate XML round trip changed source settings")

    lower_left, upper_right = geometry.bounding_box
    expected_lower = (-RADIUS, -RADIUS, -RADIUS)
    expected_upper = (RADIUS, RADIUS, RADIUS)
    if tuple(lower_left) != expected_lower or tuple(upper_right) != expected_upper:
        raise RuntimeError(
            "sphere geometry has unexpected bounds: "
            f"{tuple(lower_left)} to {tuple(upper_right)}"
        )


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, write the fixture, and return a shell-friendly status."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic OpenMC sphere/material/universe XML "
            "fixture without transport, downloads, or native-library loading."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory for generated materials.xml, geometry.xml, settings.xml, and model.xml",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir.expanduser().resolve()

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        model = build_model()
        model.export_to_xml(directory=output_dir)
        model.export_to_model_xml(path=output_dir / "model.xml")
        _validate_fixture(output_dir)
    except Exception as exc:
        print(f"ERROR: could not build OpenMC XML fixture in {output_dir}: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote validated OpenMC XML fixture to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
