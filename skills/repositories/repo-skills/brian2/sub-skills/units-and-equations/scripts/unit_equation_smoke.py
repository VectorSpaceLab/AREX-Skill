#!/usr/bin/env python3
"""Run tiny, read-only Brian2 2.9.0 units/equation checks.

The checks use the runtime NumPy target only. They create in-memory objects,
do not plot, write files, access the network, compile standalone code, or run
Brian's native test suite. Run ``--help`` to inspect the bounded options and
``--all`` for the complete fixture.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny Brian2 unit, equation-parser, namespace, function, "
            "noise, and state-updater checks."
        )
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run every bounded check (the recommended smoke invocation).",
    )
    parser.add_argument(
        "--units",
        action="store_true",
        help="Check quantities, check_units, Function, and a dimensional failure.",
    )
    parser.add_argument(
        "--equations",
        action="store_true",
        help="Check declarations, flags, namespaces, parser limits, and xi names.",
    )
    parser.add_argument(
        "--methods",
        action="store_true",
        help="Compare exact and Euler on a one-state decay and check finite noise.",
    )
    return parser


def _brian():
    try:
        import brian2  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Brian2 could not be imported; run this smoke in the prepared "
            "Brian2 2.9.0 environment."
        ) from exc
    return brian2


def check_units_and_functions() -> None:
    brian2 = _brian()
    import numpy as np  # noqa: PLC0415
    from brian2 import (
        Function,
        Network,
        NeuronGroup,
        check_units,
        implementation,
        ms,
        mV,
        prefs,
        start_scope,
        volt,
    )
    from brian2.units.fundamentalunits import DimensionMismatchError

    start_scope()
    prefs.codegen.target = "numpy"

    @check_units(x=volt, result=volt)
    def twice_voltage(x):
        return 2 * x

    # ``implementation`` is deliberately outermost, matching Brian's public
    # decorator contract. This NumPy-only variant receives raw base-unit
    # numbers during generated execution but remains unit-aware for direct
    # Python calls.
    @implementation("numpy", discard_units=True)
    @check_units(x=volt, result=volt)
    def twice_voltage_fast(x):
        return 2 * x

    wrapped = Function(lambda x: 2 * x, arg_units=[volt], return_unit=volt)
    assert twice_voltage(3 * mV) == 6 * mV
    assert twice_voltage_fast(3 * mV) == 6 * mV
    assert wrapped(3 * mV) == 6 * mV
    try:
        twice_voltage(1 * ms)
    except DimensionMismatchError:
        pass
    else:  # pragma: no cover - indicates a Brian contract regression
        raise AssertionError("check_units accepted a time where voltage was required")

    # Exercise a deliberately invalid dimensional operation without creating a
    # BrianObject that would be left outside a successfully running Network.
    try:
        _ = 1 * brian2.amp + 1 * volt
    except DimensionMismatchError:
        pass
    else:  # pragma: no cover - indicates unit validation did not run
        raise AssertionError("incompatible ampere and volt values were accepted")

    # A prepared function can be used from abstract code when its namespace is
    # explicit; zero duration forces owner-level parsing and unit validation.
    group = NeuronGroup(
        1,
        "dv/dt = twice_voltage(v) / tau : volt",
        method="euler",
        namespace={"tau": 1 * ms, "twice_voltage": twice_voltage},
    )
    fast_group = NeuronGroup(
        1,
        "dv/dt = twice_voltage_fast(v) / tau : volt",
        method="euler",
        namespace={"tau": 1 * ms, "twice_voltage_fast": twice_voltage_fast},
    )
    network = Network(group, fast_group)
    network.run(0 * ms, namespace={})
    assert np.isfinite(group.v_[:]).all()
    assert np.isfinite(fast_group.v_[:]).all()
    print("units/functions check passed")


def check_equations_and_namespaces() -> None:
    brian2 = _brian()
    import numpy as np  # noqa: PLC0415
    from brian2 import Equations, Network, NeuronGroup, defaultclock, ms, prefs, start_scope

    start_scope()
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.1 * ms

    eqs = Equations(
        """
        dv/dt = (-v + drive + bias*volt) / tau : volt (unless refractory)
        drive : volt
        bias : 1 (shared)
        tau_local : second (constant)
        sampled = rand() : 1 (constant over dt)
        """
    )
    assert {"v", "drive", "bias", "tau_local", "sampled"}.issubset(eqs.keys())

    group = NeuronGroup(
        2,
        eqs,
        threshold="v > 2*mV",
        reset="v = 0*volt",
        refractory=0.2 * ms,
        method="euler",
        namespace={"tau": 1 * ms},
    )
    group.drive = [0.2, 0.4] * brian2.mV
    group.bias = 0
    group.tau_local = 1 * ms
    network = Network(group)
    network.run(0 * ms, namespace={})
    network.run(0.2 * ms, namespace={})
    assert np.isfinite(group.v_[:]).all()

    # Brian's abstract language uses bare built-ins, not arbitrary NumPy
    # module access. This intentionally invalid expression should fail while
    # parsing, before an owner is created.
    try:
        Equations("dv/dt = np.sqrt(v) / tau : 1")
    except Exception:
        pass
    else:  # pragma: no cover - parser behavior changed unexpectedly
        raise AssertionError("np.sqrt unexpectedly passed as equation syntax")

    try:
        Equations("dv/dt = xi : 1\ndw/dt = xi : 1")
    except Exception as exc:
        assert "xi" in str(exc).lower(), str(exc)
    else:  # pragma: no cover - duplicate plain xi must be rejected
        raise AssertionError("two unsuffixed xi terms were accepted")

    print("equations/namespaces check passed")


def check_methods_and_noise() -> None:
    brian2 = _brian()
    import numpy as np  # noqa: PLC0415
    from brian2 import Network, NeuronGroup, defaultclock, exp, ms, prefs, seed, start_scope

    start_scope()
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.1 * ms
    seed(12345)

    eq = "dv/dt = -v/tau : 1"
    exact = NeuronGroup(1, eq, method="exact", namespace={"tau": 1 * ms})
    euler = NeuronGroup(1, eq, method="euler", namespace={"tau": 1 * ms})
    exact.v = 1
    euler.v = 1
    network = Network(exact, euler)
    network.run(0.2 * ms, namespace={})
    expected = float(exp(-0.2))
    assert np.isclose(exact.v_[0], expected, rtol=1e-12, atol=1e-12)
    assert np.isfinite(euler.v_[:]).all()
    assert abs(euler.v_[0] - expected) < 0.03

    noisy = NeuronGroup(
        1,
        "dx/dt = -x/tau + sigma*xi/sqrt(tau) : 1",
        method="euler",
        namespace={"tau": 1 * ms, "sigma": 0.1},
    )
    noisy.x = 0
    noisy_network = Network(noisy)
    noisy_network.run(0.2 * ms, namespace={})
    assert np.isfinite(noisy.x_[:]).all()
    print("numerical methods/noise check passed")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks: list[tuple[str, Callable[[], None]]] = []
    if args.all or not (args.units or args.equations or args.methods):
        checks = [
            ("units", check_units_and_functions),
            ("equations", check_equations_and_namespaces),
            ("methods", check_methods_and_noise),
        ]
    else:
        if args.units:
            checks.append(("units", check_units_and_functions))
        if args.equations:
            checks.append(("equations", check_equations_and_namespaces))
        if args.methods:
            checks.append(("methods", check_methods_and_noise))

    try:
        for _, check in checks:
            check()
    except (AssertionError, RuntimeError) as exc:
        print(f"unit/equation smoke failed: {exc}", file=sys.stderr)
        return 1
    print(f"unit/equation smoke passed: {len(checks)} check group(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
