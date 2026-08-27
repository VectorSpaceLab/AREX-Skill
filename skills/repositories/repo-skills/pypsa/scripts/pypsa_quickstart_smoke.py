#!/usr/bin/env python3
"""Run a self-contained PyPSA quickstart smoke.

The smoke builds a tiny electricity network with explicit carrier rows, validates
it, prints a JSON summary, and optionally runs a tiny HiGHS optimization. It
performs no network access and does not write files.

Examples:
    python pypsa_quickstart_smoke.py
    python pypsa_quickstart_smoke.py --solve
"""

from __future__ import annotations

import argparse
import json
import logging
import warnings

logging.getLogger("pypsa.version").setLevel(logging.ERROR)
warnings.filterwarnings(
    "ignore",
    message=r"pandas infers the `str` dtype for string data since its version 3\.0.*",
    category=FutureWarning,
)


def build_network():
    import pandas as pd
    import pypsa

    snapshots = pd.date_range("2024-01-01", periods=3, freq="h")
    n = pypsa.Network(name="pypsa-quickstart-smoke")
    n.set_snapshots(snapshots)

    n.add("Carrier", "AC", nice_name="electricity", color="#1f77b4")
    n.add("Carrier", "wind", nice_name="wind", color="#2ca02c")
    n.add("Carrier", "gas", nice_name="gas", color="#8c564b")
    n.add("Carrier", "load", nice_name="load", color="#7f7f7f")

    n.add("Bus", ["north", "south"], carrier="AC", v_nom=110, x=[0.0, 1.0], y=[0.0, 0.0])
    n.add("Line", "north-south", bus0="north", bus1="south", carrier="AC", r=0.01, x=0.1, s_nom=100.0)
    n.add("Generator", "wind", bus="north", carrier="wind", p_nom=20.0, p_max_pu=[0.4, 0.8, 0.5], marginal_cost=0.0)
    n.add("Generator", "gas", bus="south", carrier="gas", p_nom=20.0, marginal_cost=35.0)
    n.add("Load", "demand", bus="south", carrier="load", p_set=[8.0, 12.0, 10.0])
    n.consistency_check(strict=["unknown_buses", "unknown_carriers"])
    return n


def series_records(series) -> list[dict[str, object]]:
    """Serialize a pandas Series with possibly tuple/MultiIndex labels."""
    records: list[dict[str, object]] = []
    for key, value in series.items():
        if isinstance(key, tuple):
            label: object = [str(part) for part in key]
        else:
            label = str(key)
        records.append({"label": label, "value": float(value)})
    return records


def summarize(n, solved: bool) -> dict[str, object]:
    installed_capacity = n.statistics.installed_capacity(
        groupby="carrier", nice_names=False, drop_zero=False
    )
    summary: dict[str, object] = {
        "name": n.name,
        "snapshots": [str(s) for s in n.snapshots],
        "components": {
            component.name: int(len(component.static))
            for component in n.components.values()
            if not component.static.empty
        },
        "installed_capacity_by_carrier": series_records(installed_capacity),
        "solved": solved,
    }
    if solved:
        energy_balance = n.statistics.energy_balance(
            groupby=["carrier", "bus_carrier"], nice_names=False
        )
        summary["objective"] = float(n.objective)
        summary["energy_balance"] = series_records(energy_balance)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and optionally solve a tiny PyPSA network.")
    parser.add_argument(
        "--solve",
        action="store_true",
        help="Also run a tiny HiGHS optimization and include solved statistics.",
    )
    args = parser.parse_args()

    n = build_network()
    if args.solve:
        status, condition = n.optimize(
            solver_name="highs",
            log_to_console=False,
            include_objective_constant=False,
        )
        if (status, condition) != ("ok", "optimal"):
            raise SystemExit(f"Expected ('ok', 'optimal'), got {(status, condition)!r}")
    print(json.dumps(summarize(n, args.solve), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
