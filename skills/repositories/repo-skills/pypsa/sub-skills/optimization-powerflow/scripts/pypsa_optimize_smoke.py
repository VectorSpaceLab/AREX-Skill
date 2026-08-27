#!/usr/bin/env python3
"""Tiny PyPSA optimization smoke with a custom-constraint follow-up.

The script builds a self-contained network, solves it with HiGHS, and then
rebuilds the model to show the create-model / solve-model workflow.
"""

from __future__ import annotations

import argparse
import logging
import warnings


def suppress_pypsa_import_noise() -> None:
    warnings.filterwarnings(
        "ignore",
        message=r"pandas infers the `str` dtype for string data since its version 3\.0.*",
        category=FutureWarning,
    )
    logging.getLogger("pypsa.version").setLevel(logging.ERROR)


def build_network():
    suppress_pypsa_import_noise()
    import pandas as pd
    import pypsa

    snapshots = pd.date_range("2024-01-01", periods=3, freq="h")
    n = pypsa.Network()
    n.set_snapshots(snapshots)

    for carrier in ("AC", "gas"):
        n.add("Carrier", carrier)

    n.add("Bus", ["north", "mid", "south"], carrier="AC", v_nom=110)
    n.add(
        "Line",
        "north_mid",
        bus0="north",
        bus1="mid",
        carrier="AC",
        x=0.01,
        r=0.001,
        s_nom=100,
    )
    n.add(
        "Line",
        "mid_south",
        bus0="mid",
        bus1="south",
        carrier="AC",
        x=0.015,
        r=0.001,
        s_nom=100,
    )
    n.add(
        "Generator",
        "cheap",
        bus="north",
        carrier="gas",
        p_nom=15,
        p_nom_extendable=True,
        capital_cost=1.0,
        marginal_cost=5.0,
    )
    n.add(
        "Generator",
        "mid",
        bus="mid",
        carrier="gas",
        p_nom=20,
        marginal_cost=25.0,
    )
    load = pd.Series([25.0, 30.0, 35.0], index=snapshots)
    n.add("Load", "south_load", bus="south", carrier="AC", p_set=load)

    return n


def solve_default(include_objective_constant: bool) -> None:
    n = build_network()
    n.consistency_check(strict=["unknown_buses", "unknown_carriers"])

    status, condition = n.optimize(
        solver_name="highs",
        log_to_console=False,
        include_objective_constant=include_objective_constant,
    )

    print(f"default_solve_status={status}")
    print(f"default_solve_condition={condition}")
    print(f"objective={float(n.objective):.6f}")
    print(f"objective_constant={float(n.objective_constant):.6f}")
    print(f"cheap_p_nom_opt={float(n.c.generators.static.loc['cheap', 'p_nom_opt']):.6f}")
    print(f"cheap_dispatch_total={float(n.c.generators.dynamic.p['cheap'].sum()):.6f}")


def solve_with_custom_constraint(include_objective_constant: bool) -> None:
    n = build_network()
    n.consistency_check(strict=["unknown_buses", "unknown_carriers"])

    n.optimize.create_model(include_objective_constant=include_objective_constant)
    m = n.model
    m.add_constraints(
        m.variables["Generator-p"].sum() <= 1e6,
        name="custom_total_dispatch_cap",
    )

    status, condition = n.optimize.solve_model(
        solver_name="highs",
        log_to_console=False,
    )

    custom_dual = float(n.model.constraints["custom_total_dispatch_cap"].dual)
    print(f"custom_solve_status={status}")
    print(f"custom_solve_condition={condition}")
    print(f"custom_total_dispatch_cap_dual={custom_dual:.6f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Solve a tiny PyPSA optimization model and then repeat the solve with "
            "a custom Linopy constraint."
        )
    )
    parser.add_argument(
        "--include-objective-constant",
        action="store_true",
        help=(
            "Include the existing-capacity objective constant explicitly. "
            "Leave it off for the numerically cleaner LP path."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    solve_default(args.include_objective_constant)
    solve_with_custom_constraint(args.include_objective_constant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
