"""Build a deterministic tiny PyPSA network for modeling smoke checks.

The script performs no network access, creates no files, and does not solve an
optimization or power-flow problem. It requires PyPSA to be importable in the
current environment.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import logging

logging.getLogger("pypsa").setLevel(logging.ERROR)
logging.getLogger("pypsa.version").setLevel(logging.ERROR)

import pandas as pd
import pypsa


CARRIER_ROWS: dict[str, dict[str, Any]] = {
    "AC": {"nice_name": "electricity", "color": "#1f77b4"},
    "wind": {"nice_name": "wind", "color": "#2ca02c"},
    "gas": {"nice_name": "gas", "color": "#8c564b", "co2_emissions": 0.2},
    "demand": {"nice_name": "demand", "color": "#7f7f7f"},
}


def add_carriers(n: pypsa.Network) -> None:
    """Add all carriers used by the tiny network."""
    for carrier, attrs in CARRIER_ROWS.items():
        n.add("Carrier", carrier, **attrs)


def build_network(with_time_series: bool = False) -> pypsa.Network:
    """Return a tiny deterministic network with explicit carrier rows."""
    n = pypsa.Network(name="tiny-network-modeling")
    add_carriers(n)

    if with_time_series:
        n.set_snapshots(pd.date_range("2024-01-01 00:00", periods=3, freq="h"))

    n.add(
        "Bus",
        ["north", "south"],
        carrier="AC",
        v_nom=110.0,
        x=[0.0, 1.0],
        y=[0.0, 0.0],
    )
    n.add(
        "Line",
        "north-south",
        bus0="north",
        bus1="south",
        r=0.01,
        x=0.1,
        s_nom=100.0,
        carrier="AC",
    )
    n.add(
        "Generator",
        "gas-north",
        bus="north",
        carrier="gas",
        p_nom=50.0,
        marginal_cost=40.0,
    )

    if with_time_series:
        wind_profile = pd.Series([0.2, 0.5, 0.8], index=n.snapshots, name="wind-south")
        n.add(
            "Generator",
            "wind-south",
            bus="south",
            carrier="wind",
            p_nom=30.0,
            marginal_cost=0.0,
            p_max_pu=wind_profile,
        )

        load_names = pd.Index(["load-north", "load-south"], name="name")
        load_buses = pd.Series(["north", "south"], index=load_names)
        p_set = pd.DataFrame(
            [[12.0, 8.0], [14.0, 7.0], [13.0, 9.0]],
            index=n.snapshots,
            columns=load_names,
        )
        n.add("Load", load_names, bus=load_buses, carrier="demand", p_set=p_set)
    else:
        n.add(
            "Generator",
            "wind-south",
            bus="south",
            carrier="wind",
            p_nom=30.0,
            marginal_cost=0.0,
            p_max_pu=0.5,
        )
        n.add("Load", "load-south", bus="south", carrier="demand", p_set=20.0)

    n.calculate_dependent_values()
    return n


def check_network(n: pypsa.Network) -> None:
    """Run quick structural assertions suitable for a tiny modeling smoke."""
    n.consistency_check(strict=["unknown_buses", "unknown_carriers", "time_series"])

    required_carriers = set(CARRIER_ROWS)
    missing_carriers = required_carriers.difference(set(n.c.carriers.names))
    if missing_carriers:
        raise AssertionError(f"Missing carriers: {sorted(missing_carriers)}")

    for component_name in ["Bus", "Carrier", "Generator", "Load", "Line"]:
        if n.c[component_name].static.empty:
            raise AssertionError(f"Expected non-empty {component_name} table")

    copied = n.copy()
    if not n.equals(copied):
        raise AssertionError("Network copy is not equal to original")


def summarize(n: pypsa.Network, new_components_api: bool, checked: bool) -> dict[str, Any]:
    """Create a JSON-serializable summary of the tiny network."""
    components = {
        component.name: int(len(component.static))
        for component in n.components.values()
        if not component.static.empty
    }
    dynamic_tables = {
        component.list_name: sorted(
            attr for attr, table in component.dynamic.items() if not table.empty
        )
        for component in n.components.values()
        if any(not table.empty for table in component.dynamic.values())
    }

    generator_accessor = n.generators
    summary: dict[str, Any] = {
        "name": n.name,
        "snapshots": [str(snapshot) for snapshot in n.snapshots],
        "components": components,
        "dynamic_tables": dynamic_tables,
        "carriers": sorted(map(str, n.c.carriers.names)),
        "buses": sorted(map(str, n.c.buses.names)),
        "line_x_pu_eff": float(n.c.lines.static.loc["north-south", "x_pu_eff"]),
        "new_components_api_requested": new_components_api,
        "generator_accessor_type": type(generator_accessor).__name__,
        "checked": checked,
    }

    if new_components_api:
        summary["new_api_generators_static_rows"] = int(len(generator_accessor.static))
        summary["new_api_generators_dynamic_keys"] = sorted(
            attr for attr, table in generator_accessor.dynamic.items() if not table.empty
        )

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny self-contained PyPSA Network with explicit Carrier rows. "
            "The script prints a JSON summary and performs no solves or file writes."
        )
    )
    parser.add_argument(
        "--with-time-series",
        action="store_true",
        help="Use three hourly snapshots and labeled dynamic Load/Generator tables.",
    )
    parser.add_argument(
        "--new-components-api",
        action="store_true",
        help="Run inside pypsa.option_context('api.new_components_api', True).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run a quick consistency check and copy/equality assertion.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    option_pairs: list[Any] = [
        "general.allow_network_requests",
        False,
        "api.legacy_string_dtype",
        False,
    ]
    if args.new_components_api:
        option_pairs.extend(["api.new_components_api", True])

    with pypsa.option_context(*option_pairs):
        network = build_network(with_time_series=args.with_time_series)
        if args.check:
            check_network(network)
        summary = summarize(network, args.new_components_api, args.check)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
