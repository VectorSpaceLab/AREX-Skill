#!/usr/bin/env python3
"""Tiny PyPSA linear and non-linear power-flow smoke.

The script builds a self-contained network, solves a tiny optimization problem
to obtain dispatch, runs linear power flow, and then runs non-linear power flow
with seeded distributed slack. An optional combined optimize-then-PF pass is
available for direct helper coverage.
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
        "north_gen",
        bus="north",
        carrier="gas",
        p_nom=15,
        p_nom_extendable=True,
        capital_cost=1.0,
        marginal_cost=5.0,
    )
    n.add(
        "Generator",
        "mid_gen",
        bus="mid",
        carrier="gas",
        p_nom=20,
        marginal_cost=25.0,
        control="PV",
    )
    load = pd.Series([25.0, 30.0, 35.0], index=snapshots)
    n.add("Load", "south_load", bus="south", carrier="AC", p_set=load)

    return n


def solve_and_flow(include_objective_constant: bool) -> None:
    n = build_network()
    n.consistency_check(strict=["unknown_buses", "unknown_carriers"])

    status, condition = n.optimize(
        solver_name="highs",
        log_to_console=False,
        include_objective_constant=include_objective_constant,
    )
    print(f"opt_status={status}")
    print(f"opt_condition={condition}")

    n.optimize.fix_optimal_dispatch()
    n.lpf()
    lpf_line_flow = float(n.lines_t.p0.loc[n.snapshots[0], "north_mid"])
    print(f"lpf_north_mid_p0={lpf_line_flow:.6f}")

    pf_result = n.pf(
        use_seed=True,
        distribute_slack=True,
        slack_weights="p_nom_opt",
    )
    pf_converged = bool(pf_result["converged"].to_numpy().all())
    print(f"pf_converged={pf_converged}")

    v_mag = float(n.buses_t.v_mag_pu.loc[n.snapshots[0], "south"])
    print(f"south_v_mag_pu={v_mag:.6f}")


def run_combined_helper(include_objective_constant: bool) -> None:
    n = build_network()
    n.consistency_check(strict=["unknown_buses", "unknown_carriers"])

    combined = n.optimize.optimize_and_run_non_linear_powerflow(
        solver_name="highs",
        log_to_console=False,
        include_objective_constant=include_objective_constant,
        use_seed=True,
        distribute_slack=True,
        slack_weights="p_nom_opt",
    )
    combined_converged = bool(combined["converged"].to_numpy().all())
    print(f"combined_status={combined['status']}")
    print(f"combined_condition={combined['termination_condition']}")
    print(f"combined_pf_converged={combined_converged}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Solve a tiny PyPSA network, run linear and non-linear power flow, and "
            "optionally exercise the combined optimize-then-PF helper."
        )
    )
    parser.add_argument(
        "--include-objective-constant",
        action="store_true",
        help=(
            "Include the existing-capacity objective constant explicitly during the "
            "optimization pre-step."
        ),
    )
    parser.add_argument(
        "--run-combined",
        action="store_true",
        help="Also run optimize_and_run_non_linear_powerflow() on a fresh copy.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    solve_and_flow(args.include_objective_constant)
    if args.run_combined:
        run_combined_helper(args.include_objective_constant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
