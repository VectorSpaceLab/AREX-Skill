#!/usr/bin/env python3
"""Smoke test for PyPSA temporal and spatial clustering.

This helper builds a tiny self-contained network, checks base temporal
resampling/downsampling, exercises manual busmap aggregation, and optionally
runs scikit-learn or TSAM-backed clustering if those packages are installed.

Prerequisites:
- PyPSA with its base clustering stack.
- Optional: scikit-learn for k-means/HAC busmap creation.
- Optional: TSAM for temporal segmentation.
- Safe by default: no network access, no file writes, and no plotting.

Example:
    python pypsa_clustering_smoke.py
"""

from __future__ import annotations

import argparse
import logging
import warnings
from importlib.util import find_spec

logging.getLogger("pypsa.version").setLevel(logging.ERROR)
warnings.filterwarnings(
    "ignore",
    message=r"pandas infers the `str` dtype for string data since its version 3\.0.*",
    category=FutureWarning,
)

import numpy as np
import pandas as pd

import pypsa


def build_network(name: str = "cluster-smoke") -> pypsa.Network:
    """Create a tiny network with enough time-varying data for clustering."""
    snapshots = pd.date_range("2024-01-01", periods=24, freq="h")
    wind_profile = [0.2, 0.3, 0.4, 0.6, 0.7, 0.8] * 4
    load_profile = [4.0, 5.0, 6.0, 7.0, 6.0, 5.0] * 4

    n = pypsa.Network(name=name)
    n.set_snapshots(snapshots)

    n.add("Carrier", "AC", nice_name="AC", color="#4C78A8")
    n.add("Carrier", "wind", nice_name="Wind", color="#54A24B")
    n.add("Carrier", "gas", nice_name="Gas", color="#E45756")
    n.add("Carrier", "load", nice_name="Load", color="#72B7B2")

    buses = {
        "b0": (0.0, 0.0),
        "b1": (1.0, 0.0),
        "b2": (0.0, 1.0),
        "b3": (1.0, 1.0),
    }
    for bus, (x, y) in buses.items():
        n.add("Bus", bus, carrier="AC", x=x, y=y, country="DE")

    for name_, bus0, bus1 in [
        ("line01", "b0", "b1"),
        ("line13", "b1", "b3"),
        ("line32", "b3", "b2"),
        ("line20", "b2", "b0"),
    ]:
        n.add("Line", name_, bus0=bus0, bus1=bus1, r=0.01, x=0.1, s_nom=100.0)

    n.add(
        "Generator",
        "wind_gen",
        bus="b0",
        carrier="wind",
        p_nom=12.0,
        p_max_pu=wind_profile,
        marginal_cost=0.0,
    )
    n.add(
        "Generator",
        "gas_gen",
        bus="b3",
        carrier="gas",
        p_nom=20.0,
        p_max_pu=1.0,
        marginal_cost=25.0,
    )
    n.add("Load", "load_w", bus="b1", carrier="load", p_set=load_profile)
    n.add("Load", "load_e", bus="b2", carrier="load", p_set=[v * 1.1 for v in load_profile])

    n.consistency_check()
    return n


def run_temporal_smoke(n: pypsa.Network) -> None:
    """Exercise base temporal clustering and optional TSAM segmentation."""
    resampled = n.cluster.temporal.get_resample_result("6h")
    if len(resampled.n.snapshots) != 4:
        raise AssertionError("resample('6h') should reduce 24 hourly snapshots to 4")
    if not resampled.snapshot_map.index.equals(n.snapshots):
        raise AssertionError("resample snapshot map must cover the original snapshots")
    if not np.isclose(
        resampled.n.snapshot_weightings["objective"].sum(),
        n.snapshot_weightings["objective"].sum(),
    ):
        raise AssertionError("resample should preserve total modeled hours")

    downsampled = n.cluster.temporal.get_downsample_result(4)
    if len(downsampled.n.snapshots) != 6:
        raise AssertionError("downsample(4) should reduce 24 hourly snapshots to 6")
    if not np.isclose(
        downsampled.n.snapshot_weightings["objective"].sum(),
        n.snapshot_weightings["objective"].sum(),
    ):
        raise AssertionError("downsample should preserve total modeled hours")

    if find_spec("tsam") is None:
        print("[clustering] skipping TSAM segment: optional dependency 'tsam' not installed")
    else:
        segmented = n.cluster.temporal.segment(4)
        if len(segmented.snapshots) != 4:
            raise AssertionError("segment(4) should return 4 representative snapshots")
        if not np.isclose(
            segmented.snapshot_weightings["objective"].sum(),
            n.snapshot_weightings["objective"].sum(),
        ):
            raise AssertionError("segment should preserve total modeled hours")


def run_spatial_smoke(n: pypsa.Network) -> None:
    """Exercise manual busmap aggregation and optional scikit-learn busmaps."""
    manual_busmap = pd.Series(
        {"b0": "west", "b1": "west", "b2": "east", "b3": "east"},
        name="busmap",
    )
    clustered = n.cluster.spatial.cluster_by_busmap(manual_busmap)
    if len(clustered.buses) != 2:
        raise AssertionError("manual busmap clustering should yield two buses")

    result = n.cluster.spatial.get_clustering_from_busmap(manual_busmap)
    if len(result.n.buses) != 2:
        raise AssertionError("get_clustering_from_busmap should yield two buses")
    if not result.busmap.equals(manual_busmap):
        raise AssertionError("returned busmap should match the manual input")

    if find_spec("sklearn") is None:
        print(
            "[clustering] skipping scikit-learn busmap creation: optional dependency 'sklearn' not installed"
        )
        return

    weights = pd.Series(1, index=n.c.buses.static.index)
    kmeans_busmap = n.cluster.spatial.busmap_by_kmeans(
        bus_weightings=weights,
        n_clusters=2,
        random_state=0,
    )
    kmeans_clustered = n.cluster.spatial.cluster_by_busmap(kmeans_busmap)
    if len(kmeans_clustered.buses) != 2:
        raise AssertionError("k-means busmap clustering should yield two buses")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny clustering smoke test for PyPSA."
    )
    parser.parse_args(argv)

    n = build_network()
    run_temporal_smoke(n)
    run_spatial_smoke(n)

    print("[clustering] ok: temporal clustering and spatial busmap aggregation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
