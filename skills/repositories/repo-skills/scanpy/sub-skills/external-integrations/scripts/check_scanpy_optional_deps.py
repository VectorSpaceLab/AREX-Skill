#!/usr/bin/env python3
"""Check availability of Scanpy optional dependency features without installing packages."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from typing import Any

FEATURES: dict[str, dict[str, Any]] = {
    "bbknn": {
        "extra": "scanpy[bbknn]",
        "modules": ["bbknn"],
        "packages": ["bbknn"],
        "summary": "scanpy.external.pp.bbknn batch-balanced neighbors",
    },
    "cellbrowser": {
        "extra": None,
        "modules": ["cellbrowser"],
        "packages": ["cellbrowser"],
        "summary": "scanpy.external.exporting.cellbrowser exporter",
    },
    "dask": {
        "extra": "scanpy[dask]",
        "modules": ["dask", "dask.array"],
        "packages": ["dask"],
        "summary": "selected Dask-backed AnnData and preprocessing support",
    },
    "dask-ml": {
        "extra": "scanpy[dask-ml]",
        "modules": ["dask", "dask.array", "dask_ml"],
        "packages": ["dask", "dask-ml"],
        "summary": "Dask-ML backed PCA paths",
    },
    "harmony-timeseries": {
        "extra": None,
        "modules": ["harmony"],
        "packages": ["harmonyTS"],
        "summary": "scanpy.external.tl.harmony_timeseries from harmonyTS",
    },
    "leiden": {
        "extra": "scanpy[leiden]",
        "modules": ["igraph", "leidenalg"],
        "packages": ["igraph", "leidenalg"],
        "summary": "Leiden clustering with leidenalg/igraph",
    },
    "louvain": {
        "extra": "scanpy[louvain]",
        "modules": ["igraph", "louvain"],
        "packages": ["igraph", "louvain"],
        "summary": "Louvain clustering support",
    },
    "magic": {
        "extra": "scanpy[magic]",
        "modules": ["magic"],
        "packages": ["magic-impute"],
        "summary": "scanpy.external.pp.magic imputation",
    },
    "mnn": {
        "extra": None,
        "modules": ["mnnpy"],
        "packages": ["mnnpy"],
        "summary": "scanpy.external.pp.mnn_correct",
    },
    "paga": {
        "extra": "scanpy[paga]",
        "modules": ["igraph"],
        "packages": ["igraph"],
        "summary": "PAGA graph abstraction support",
    },
    "palantir": {
        "extra": None,
        "modules": ["palantir"],
        "packages": ["palantir"],
        "summary": "scanpy.external.tl.palantir and palantir_results",
    },
    "phate": {
        "extra": None,
        "modules": ["phate"],
        "packages": ["phate"],
        "summary": "scanpy.external.tl.phate and pl.phate",
    },
    "phenograph": {
        "extra": None,
        "modules": ["phenograph"],
        "packages": ["phenograph"],
        "summary": "scanpy.external.tl.phenograph",
    },
    "plotting": {
        "extra": "scanpy[plotting]",
        "modules": ["colour"],
        "packages": ["colour-science"],
        "summary": "optional colour-science plotting support",
    },
    "pypairs": {
        "extra": None,
        "modules": ["pypairs"],
        "packages": ["pypairs"],
        "summary": "scanpy.external.tl.sandbag and cyclone",
    },
    "rapids": {
        "extra": None,
        "modules": ["rapids_singlecell", "cuml"],
        "packages": ["rapids-singlecell", "cuml"],
        "summary": "separate RAPIDS single-cell GPU stack and cuML neighbor backend, not a Scanpy extra",
    },
    "sam": {
        "extra": None,
        "modules": ["samalg"],
        "packages": ["sc-sam"],
        "summary": "scanpy.external.tl.sam from sc-sam",
    },
    "scanorama": {
        "extra": "scanpy[scanorama]",
        "modules": ["scanorama"],
        "packages": ["scanorama"],
        "summary": "scanpy.external.pp.scanorama_integrate",
    },
    "scanpy2": {
        "extra": "scanpy[scanpy2]",
        "modules": ["igraph", "skmisc"],
        "packages": ["igraph", "scikit-misc"],
        "summary": "preview-style combo of Leiden graph tooling and Seurat v3 HVG support",
    },
    "scrublet": {
        "extra": "scanpy[scrublet]",
        "modules": ["skimage"],
        "packages": ["scikit-image"],
        "summary": "scanpy.pp.scrublet optional scikit-image dependency",
    },
    "skmisc": {
        "extra": "scanpy[skmisc]",
        "modules": ["skmisc"],
        "packages": ["scikit-misc"],
        "summary": "highly_variable_genes seurat_v3 flavors",
    },
    "trimap": {
        "extra": None,
        "modules": ["trimap"],
        "packages": ["trimap"],
        "summary": "scanpy.external.tl.trimap and pl.trimap",
    },
    "wishbone": {
        "extra": None,
        "modules": ["wishbone"],
        "packages": ["wishbone"],
        "summary": "scanpy.external.tl.wishbone and trajectory plotting",
    },
}


def module_present(module: str) -> bool:
    """Return whether a module can be found without importing it."""
    return find_spec(module) is not None


def package_version(package: str) -> str | None:
    """Return installed distribution version without importing the package."""
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def check_feature(name: str) -> dict[str, Any]:
    """Build a dependency availability record for one feature."""
    feature = FEATURES[name]
    modules = feature["modules"]
    packages = feature.get("packages", [])
    present = [module for module in modules if module_present(module)]
    missing = [module for module in modules if module not in present]
    versions = {package: package_version(package) for package in packages}
    return {
        "feature": name,
        "summary": feature["summary"],
        "extra": feature["extra"],
        "present": present,
        "missing": missing,
        "available": not missing,
        "versions": versions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report optional dependency availability for Scanpy features using "
            "importlib.util.find_spec and package metadata only. No packages are installed."
        )
    )
    parser.add_argument(
        "--feature",
        action="append",
        choices=sorted(FEATURES),
        help="Feature to check. May be passed multiple times. Defaults to all features.",
    )
    parser.add_argument(
        "--list-features",
        action="store_true",
        help="List known feature keys with summaries and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a readable text report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_features:
        rows = [
            {
                "feature": name,
                "summary": data["summary"],
                "extra": data["extra"],
                "modules": data["modules"],
                "packages": data.get("packages", []),
            }
            for name, data in sorted(FEATURES.items())
        ]
        if args.json:
            print(json.dumps(rows, indent=2, sort_keys=True))
        else:
            for row in rows:
                extra = row["extra"] or "no Scanpy extra; install upstream package only if needed"
                modules = ", ".join(row["modules"])
                packages = ", ".join(row["packages"]) or "none"
                print(f"{row['feature']}: {row['summary']} | {extra} | modules: {modules} | packages: {packages}")
        return 0

    selected = args.feature or sorted(FEATURES)
    results = [check_feature(name) for name in selected]

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for result in results:
            status = "available" if result["available"] else "missing"
            extra = result["extra"] or "install named upstream package only if needed"
            present = ", ".join(result["present"]) or "none"
            missing = ", ".join(result["missing"]) or "none"
            versions = ", ".join(
                f"{package}={installed or 'not installed'}"
                for package, installed in result["versions"].items()
            ) or "none"
            print(f"{result['feature']}: {status}")
            print(f"  summary: {result['summary']}")
            print(f"  install: {extra}")
            print(f"  present modules: {present}")
            print(f"  missing modules: {missing}")
            print(f"  package versions: {versions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
