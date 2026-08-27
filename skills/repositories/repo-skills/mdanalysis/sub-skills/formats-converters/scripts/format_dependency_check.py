#!/usr/bin/env python3
"""Report MDAnalysis optional format/converter dependency availability.

This helper is intentionally read-only and offline. It imports MDAnalysis to
show the installed version, then uses importlib.util.find_spec for optional
packages so heavy libraries are not imported just to check availability.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from importlib import metadata


@dataclass(frozen=True)
class OptionalDependency:
    key: str
    import_name: str
    package_hint: str
    mdanalysis_area: str
    install_hint: str
    purpose: str


OPTIONAL_DEPENDENCIES = [
    OptionalDependency(
        key="h5md",
        import_name="h5py",
        package_hint="h5py>=2.10",
        mdanalysis_area="coordinates.H5MD",
        install_hint="Install h5py for H5MD .h5md read/write support.",
        purpose="H5MD trajectories and H5MDWriter",
    ),
    OptionalDependency(
        key="chemfiles",
        import_name="chemfiles",
        package_hint="chemfiles>=0.10",
        mdanalysis_area="coordinates.chemfiles",
        install_hint="Install chemfiles and use format='CHEMFILES' for the Chemfiles backend.",
        purpose="Chemfiles-backed coordinate reading/writing",
    ),
    OptionalDependency(
        key="parmed",
        import_name="parmed",
        package_hint="parmed",
        mdanalysis_area="converters.ParmEd",
        install_hint="Install parmed for ParmEd Structure import/export.",
        purpose="ParmEd converter and object reader",
    ),
    OptionalDependency(
        key="openmm",
        import_name="openmm",
        package_hint="openmm",
        mdanalysis_area="converters.OpenMM/OpenMMParser",
        install_hint="Install OpenMM for OpenMM Topology, Simulation, PDBFile, Modeller, or PDBxFile object imports.",
        purpose="OpenMM object reader/parser interoperability",
    ),
    OptionalDependency(
        key="pdb_fetch",
        import_name="pooch",
        package_hint="pooch",
        mdanalysis_area="fetch.from_PDB",
        install_hint="Install pooch for MDAnalysis.fetch.from_PDB; network access is still required.",
        purpose="RCSB PDB downloader/cache helper",
    ),
    OptionalDependency(
        key="edr_auxiliary",
        import_name="pyedr",
        package_hint="pyedr>=0.7.0",
        mdanalysis_area="auxiliary.EDR",
        install_hint="Install pyedr for GROMACS .edr auxiliary data.",
        purpose="GROMACS EDR auxiliary energy/time-series reader",
    ),
    OptionalDependency(
        key="tng",
        import_name="pytng",
        package_hint="pytng>=0.2.3",
        mdanalysis_area="coordinates.TNG",
        install_hint="Install pytng for TNG trajectory reading; MDAnalysis has no TNG writer.",
        purpose="GROMACS TNG trajectory reader",
    ),
    OptionalDependency(
        key="gsd",
        import_name="gsd",
        package_hint="gsd>3.0.0",
        mdanalysis_area="coordinates.GSD/topology.GSDParser",
        install_hint="Install gsd for HOOMD GSD topology and trajectory files.",
        purpose="HOOMD GSD read support",
    ),
    OptionalDependency(
        key="rdkit",
        import_name="rdkit",
        package_hint="rdkit>=2022.09.1",
        mdanalysis_area="converters.RDKit",
        install_hint="Install RDKit for RDKit molecule import/export and SMARTS-related workflows.",
        purpose="RDKit reader/converter interoperability",
    ),
    OptionalDependency(
        key="imd",
        import_name="imdclient",
        package_hint="imdclient>=0.2.2",
        mdanalysis_area="coordinates.IMD",
        install_hint="Install imdclient for authorized live IMDv3 socket streams.",
        purpose="Interactive Molecular Dynamics stream reader",
    ),
    OptionalDependency(
        key="netcdf_writer",
        import_name="netCDF4",
        package_hint="netCDF4>=1.0",
        mdanalysis_area="coordinates.TRJ.NCDFWriter",
        install_hint="Install netCDF4 for faster AMBER NetCDF writing; reading can use SciPy NetCDF.",
        purpose="Fast AMBER NetCDF writer backend",
    ),
]


def find_distribution_version(import_name: str) -> str | None:
    candidates = [import_name]
    if import_name == "rdkit":
        candidates.append("rdkit-pypi")
    if import_name == "netCDF4":
        candidates.append("netcdf4")
    for candidate in candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return None


def check_optional(dep: OptionalDependency) -> dict[str, object]:
    spec = importlib.util.find_spec(dep.import_name)
    installed = spec is not None
    return {
        **asdict(dep),
        "installed": installed,
        "version": find_distribution_version(dep.import_name) if installed else None,
    }


def check_mdanalysis() -> dict[str, object]:
    try:
        import MDAnalysis as mda
    except Exception as exc:  # noqa: BLE001 - report any import failure clearly.
        return {
            "installed": False,
            "version": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {"installed": True, "version": getattr(mda, "__version__", None), "error": None}


def build_report() -> dict[str, object]:
    optional = [check_optional(dep) for dep in OPTIONAL_DEPENDENCIES]
    missing = [item for item in optional if not item["installed"]]
    installed = [item for item in optional if item["installed"]]
    return {
        "mdanalysis": check_mdanalysis(),
        "optional_dependencies": optional,
        "summary": {
            "installed_optional_count": len(installed),
            "missing_optional_count": len(missing),
            "tracked_optional_package_hints": [dep.package_hint for dep in OPTIONAL_DEPENDENCIES],
            "mdanalysis_extra_formats_group": [
                "netCDF4>=1.0",
                "h5py>=2.10",
                "chemfiles>=0.10",
                "parmed",
                "pooch",
                "pyedr>=0.7.0",
                "pytng>=0.2.3",
                "gsd>3.0.0",
                "rdkit>=2022.09.1",
                "imdclient>=0.2.2",
            ],
        },
    }


def print_text(report: dict[str, object]) -> None:
    mda_info = report["mdanalysis"]
    if mda_info["installed"]:
        print(f"MDAnalysis: installed ({mda_info['version']})")
    else:
        print("MDAnalysis: not importable")
        print(f"  error: {mda_info['error']}")

    print("\nOptional format/converter dependencies:")
    for item in report["optional_dependencies"]:
        status = "installed" if item["installed"] else "missing"
        version = f" ({item['version']})" if item["version"] else ""
        print(f"- {item['key']}: {status}{version}")
        print(f"  import: {item['import_name']} | package: {item['package_hint']}")
        print(f"  area: {item['mdanalysis_area']} | purpose: {item['purpose']}")
        if not item["installed"]:
            print(f"  guidance: {item['install_hint']}")

    missing = [item for item in report["optional_dependencies"] if not item["installed"]]
    if missing:
        print("\nInstall narrowly for the failed workflow instead of broad extras when possible.")
    else:
        print("\nAll tracked optional dependencies are discoverable in this environment.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check MDAnalysis optional format/converter dependencies without opening data files."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
