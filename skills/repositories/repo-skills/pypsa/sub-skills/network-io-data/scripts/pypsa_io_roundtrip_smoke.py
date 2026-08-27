#!/usr/bin/env python3
"""Tiny PyPSA I/O smoke test.

By default this script checks CSV-folder and netCDF round-trips on a tiny
self-contained network. Optional flags add HDF5 and Excel checks when the
matching dependencies are installed.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings(
    "ignore", message=r"The correct version of PyPSA could not be resolved.*"
)
logging.basicConfig(level=logging.ERROR)

import pandas as pd
import pypsa


def have(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def build_tiny_network() -> pypsa.Network:
    n = pypsa.Network(name="Tiny I/O Smoke")
    n.meta = {"purpose": "pypsa-io-roundtrip-smoke"}
    n.set_snapshots(pd.date_range("2025-01-01", periods=3, freq="h"))
    n.add("Carrier", "AC")
    n.add("Bus", "bus0", carrier="AC", x=0.0, y=0.0, v_nom=1.0)
    n.add("Bus", "bus1", carrier="AC", x=1.0, y=0.0, v_nom=1.0)
    n.add("Line", "line0", bus0="bus0", bus1="bus1", r=0.01, x=0.1, s_nom=100.0)
    n.add(
        "Generator",
        "gen0",
        bus="bus0",
        carrier="AC",
        p_nom=10.0,
        marginal_cost=20.0,
        p_max_pu=[1.0, 0.9, 0.8],
    )
    n.add("Load", "load0", bus="bus1", carrier="AC", p_set=[5.0, 6.0, 7.0])
    return n


def require_equal(original: pypsa.Network, loaded: pypsa.Network, label: str) -> None:
    if not original.equals(loaded, log_mode="strict"):
        raise SystemExit(f"{label} round-trip mismatch")


def run_csv_roundtrip(network: pypsa.Network, root: Path) -> None:
    export_path = root / "csv-roundtrip"
    export_path.mkdir(parents=True, exist_ok=True)
    network.export_to_csv_folder(export_path)
    reloaded = pypsa.Network(export_path)
    require_equal(network, reloaded, "CSV")
    print("[ok] CSV round-trip")


def run_netcdf_roundtrip(network: pypsa.Network, root: Path) -> None:
    export_path = root / "network.nc"
    network.export_to_netcdf(export_path)
    reloaded = pypsa.Network()
    reloaded.import_from_netcdf(export_path)
    require_equal(network, reloaded, "netCDF")
    print("[ok] netCDF round-trip")


def run_hdf5_roundtrip(network: pypsa.Network, root: Path) -> None:
    if not have("tables"):
        print("[skip] HDF5 round-trip (install pypsa[hdf5] to enable it)")
        return
    export_path = root / "network.h5"
    network.export_to_hdf5(export_path)
    reloaded = pypsa.Network()
    reloaded.import_from_hdf5(export_path)
    require_equal(network, reloaded, "HDF5")
    print("[ok] HDF5 round-trip")


def run_excel_roundtrip(network: pypsa.Network, root: Path) -> None:
    if not have("openpyxl") or not have("python_calamine"):
        print("[skip] Excel round-trip (install pypsa[excel] to enable it)")
        return
    export_path = root / "network.xlsx"
    network.export_to_excel(export_path)
    reloaded = pypsa.Network()
    reloaded.import_from_excel(export_path)
    require_equal(network, reloaded, "Excel")
    print("[ok] Excel round-trip")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny PyPSA I/O round-trips on a self-contained network."
    )
    parser.add_argument(
        "--with-hdf5",
        action="store_true",
        help="Also try an HDF5 round-trip when the optional dependency is installed.",
    )
    parser.add_argument(
        "--with-excel",
        action="store_true",
        help="Also try an Excel round-trip when the optional dependency is installed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    network = build_tiny_network()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        with pypsa.option_context("api.legacy_string_dtype", False):
            with tempfile.TemporaryDirectory(prefix="pypsa-io-smoke-") as tmp:
                root = Path(tmp)
                run_csv_roundtrip(network, root)
                run_netcdf_roundtrip(network, root)
                if args.with_hdf5:
                    run_hdf5_roundtrip(network, root)
                if args.with_excel:
                    run_excel_roundtrip(network, root)

    print("[done] PyPSA I/O smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
