#!/usr/bin/env python3
"""Smoke test for PyPSA analysis, statistics, and plotting.

This helper builds a tiny self-contained network, checks unsolved and solved
statistics, exercises static and interactive charts, draws a headless network
map, and compares two solved scenario networks in a NetworkCollection.

Prerequisites:
- PyPSA installed with its plotting/statistics dependencies.
- Optional: Plotly for interactive statistics charts, Pydeck for
  ``n.plot.explore``.
- Safe by default: no network access, no file writes, and Matplotlib uses Agg.

Example:
    python pypsa_analysis_smoke.py
"""

from __future__ import annotations

import argparse
import logging
import warnings
from typing import Iterable

logging.getLogger("pypsa.version").setLevel(logging.ERROR)
warnings.filterwarnings(
    "ignore",
    message=r"pandas infers the `str` dtype for string data since its version 3\.0.*",
    category=FutureWarning,
)

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import pandas as pd

import pypsa


def build_network(name: str, snapshot_start: str, load_scale: float = 1.0) -> pypsa.Network:
    """Build a tiny network that can be analyzed and solved quickly."""
    snapshots = pd.date_range(snapshot_start, periods=6, freq="h")
    load_profile = [6.0, 7.0, 8.0, 7.0, 6.0, 5.0]
    wind_profile = [0.3, 0.5, 0.8, 0.6, 0.4, 0.2]

    n = pypsa.Network(name=name)
    n.set_snapshots(snapshots)

    n.add("Carrier", "AC", nice_name="AC", color="#4C78A8")
    n.add("Carrier", "wind", nice_name="Wind", color="#54A24B")
    n.add("Carrier", "gas", nice_name="Gas", color="#E45756")
    n.add("Carrier", "load", nice_name="Load", color="#72B7B2")

    n.add("Bus", "bus0", carrier="AC", x=0.0, y=0.0, country="DE")
    n.add("Bus", "bus1", carrier="AC", x=1.0, y=0.4, country="DE")

    n.add(
        "Generator",
        "wind_gen",
        bus="bus0",
        carrier="wind",
        p_nom=8.0,
        p_max_pu=wind_profile,
        marginal_cost=0.0,
        capital_cost=500.0,
    )
    n.add(
        "Generator",
        "gas_gen",
        bus="bus1",
        carrier="gas",
        p_nom=20.0,
        p_max_pu=1.0,
        marginal_cost=30.0,
        capital_cost=1200.0,
    )
    n.add(
        "Load",
        "load0",
        bus="bus1",
        carrier="load",
        p_set=[value * load_scale for value in load_profile],
    )
    n.add("Line", "line0", bus0="bus0", bus1="bus1", r=0.01, x=0.1, s_nom=100.0)

    n.consistency_check()
    return n


def assert_solved_network(network: pypsa.Network) -> None:
    """Solve a tiny network and check the expected solved statistics."""
    assert network.stats is network.statistics

    installed = network.statistics.installed_capacity(
        groupby="carrier", nice_names=False, drop_zero=False
    )
    if installed.empty:
        raise AssertionError("installed_capacity should be populated before solving")

    try:
        unsolved_optimal = network.statistics.optimal_capacity()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "optimal_capacity should be callable on an unsolved network"
        ) from exc

    if not unsolved_optimal.empty:
        raise AssertionError(
            "optimal_capacity should be empty before the network is solved"
        )

    status, condition = network.optimize(
        solver_name="highs",
        log_to_console=False,
        include_objective_constant=False,
    )
    if (status, condition) != ("ok", "optimal"):
        raise RuntimeError(f"Expected an optimal HiGHS solve, got {(status, condition)!r}")

    solved_energy = network.statistics.energy_balance()
    if solved_energy.empty:
        raise AssertionError("energy_balance should be populated after solving")

    solved_prices = network.statistics.prices()
    if solved_prices.empty:
        raise AssertionError("prices should be populated after solving")

    # Headless static network map.
    fig, ax = plt.subplots(figsize=(4, 3))
    result = network.plot.map(ax=ax, geomap=False, line_flow="mean", title=network.name)
    if "nodes" not in result or "branches" not in result:
        raise AssertionError("static network map did not return expected collections")
    plt.close(fig)

    # Statistics map.
    stat_fig, _ = network.statistics.installed_capacity.plot.map(
        geomap=False,
    )
    plt.close(stat_fig)

    # Interactive statistics chart.
    try:
        plotly_fig = network.statistics.energy_balance.iplot.area(bus_carrier="AC")
    except Exception as exc:  # noqa: BLE001
        print(f"[analysis] skipping Plotly statistics chart: {exc}")
    else:
        if not getattr(plotly_fig, "data", None):
            raise AssertionError("Plotly statistics chart did not contain data")

    # Plotly network map.
    try:
        plotly_map = network.plot.iplot(iplot=False, mapbox=False, title=network.name)
    except Exception as exc:  # noqa: BLE001
        print(f"[analysis] skipping Plotly network map: {exc}")
    else:
        if not plotly_map.get("data"):
            raise AssertionError("Plotly network map did not contain data")

    # Pydeck network map.
    try:
        deck = network.plot.explore(map_style="light", tooltip=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[analysis] skipping Pydeck network map: {exc}")
    else:
        if deck is None:
            raise AssertionError("Pydeck explore returned no deck")

    plt.close("all")


def assert_collection_comparison(networks: Iterable[pypsa.Network]) -> None:
    """Compare solved networks through a NetworkCollection."""
    network_list = list(networks)
    collection = pypsa.NetworkCollection(
        network_list,
        index=pd.Index([n.name for n in network_list], name="scenario"),
    )

    balance = collection.statistics.energy_balance()
    if balance.empty:
        raise AssertionError("NetworkCollection energy_balance should not be empty")
    if "scenario" not in balance.index.names:
        raise AssertionError("NetworkCollection statistics should include scenario index")

    for network in network_list:
        expected = network.statistics.energy_balance().sort_index()
        actual = balance.xs(network.name, level="scenario").sort_index()
        pd.testing.assert_series_equal(actual, expected, check_names=False)

    fig, _, _ = collection.statistics.installed_capacity.plot.bar(
        components="Generator",
        facet_col="scenario",
    )
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny headless analysis/visualization smoke test for PyPSA."
    )
    parser.parse_args(argv)

    base = build_network("base", "2024-01-01", load_scale=1.0)
    assert_solved_network(base)

    variant = build_network("variant", "2024-02-01", load_scale=1.15)
    assert_solved_network(variant)

    assert_collection_comparison([base, variant])

    print(
        "[analysis] ok: statistics, static plots, interactive plots, and collection comparison passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
