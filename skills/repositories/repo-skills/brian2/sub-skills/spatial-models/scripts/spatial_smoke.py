#!/usr/bin/env python3
"""Run a tiny Brian2 spatial-model smoke check.

This is intentionally a bounded, CPU-oriented fixture: one spherical soma and
one short cylinder with two compartments, a passive surfacic current, and one
point-current injection. It checks construction, topology-derived indices,
units, subgroup selection, and a short simulation. It never downloads data or
runs native/standalone code.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and briefly simulate a tiny Brian2 SpatialNeuron."
    )
    parser.add_argument(
        "--duration-ms",
        type=float,
        default=0.2,
        help="bounded simulation duration in milliseconds (default: 0.2)",
    )
    parser.add_argument(
        "--constructor-only",
        action="store_true",
        help="skip the NumPy diffusion run and check construction/geometry only",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.duration_ms <= 0 or args.duration_ms > 5:
        raise SystemExit("--duration-ms must be > 0 and <= 5")

    try:
        from brian2 import (  # noqa: PLC0415 - deferred for --help
            Cylinder,
            DimensionMismatchError,
            Soma,
            SpatialNeuron,
            StateMonitor,
            cm,
            defaultclock,
            mV,
            ms,
            nA,
            ohm,
            prefs,
            run,
            siemens,
            um,
            uF,
        )
    except ImportError as exc:
        print(f"Brian2 import failed: {exc}", file=sys.stderr)
        return 2

    # Force the ordinary CPU/NumPy path; construction itself does not trigger a
    # Cython build. The actual multi-compartment NumPy run is gated below on
    # SciPy, which Brian2's supported NumPy spatial tests require. No standalone
    # project is created by this fixture.
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.01 * ms
    morph = Soma(diameter=20 * um)
    morph.axon = Cylinder(diameter=1 * um, length=20 * um, n=2)
    if morph.total_compartments != 3:
        raise AssertionError(f"unexpected compartment count: {morph.total_compartments}")
    if morph.axon.indices[:].tolist() != [1, 2]:
        raise AssertionError(f"unexpected axon indices: {morph.axon.indices[:]}")

    print(str(morph.topology()), end="")
    print(f"compartments={morph.total_compartments} axon={morph.axon.indices[:]}")

    EL = -70 * mV
    gL = 1e-4 * siemens / cm**2
    eqs = """
    Im = gL * (EL - v) : amp/meter**2
    Iinj : amp (point current)
    """
    neuron = SpatialNeuron(
        morphology=morph,
        model=eqs,
        Cm=1 * uF / cm**2,
        Ri=150 * ohm * cm,
        method="exponential_euler",
    )
    neuron.v = EL
    neuron.Iinj[0] = 0.01 * nA

    soma_index = morph.indices[0]
    distal_index = morph.axon.indices[-1]
    if soma_index != 0 or distal_index != 2:
        raise AssertionError("flattened morphology indices are not as expected")
    if not np.all(neuron.Cm[:] == 1 * uF / cm**2):
        raise AssertionError("explicit Cm was not installed on every compartment")
    if not np.all(neuron.Ri[:] == 150 * ohm * cm):
        raise AssertionError("explicit Ri was not installed")
    if float(neuron.area[soma_index] / um**2) <= 0:
        raise AssertionError("soma area must be positive")
    if not np.all(np.isfinite(np.asarray(neuron.space_constant[:]))):
        raise AssertionError("space_constant contains non-finite values")
    if not np.all(np.isfinite(np.asarray(neuron.time_constant[:]))):
        raise AssertionError("time_constant contains non-finite values")
    # Check that the point-current model contains Brian2's area conversion.
    if "Iinj/area" not in neuron.equations["Im"].expr.code:
        raise AssertionError("point current was not converted to a density")

    # Constructor-level negative checks: Im is mandatory, and point-current
    # declarations must carry amp units. Brian2 may accept a wrongly dimensioned
    # Im expression at construction, so do not claim the constructor validates
    # density units; the valid fixture above keeps Im in amp/meter**2.
    try:
        SpatialNeuron(morphology=Soma(diameter=10 * um), model="v : volt")
    except TypeError:
        pass
    else:
        raise AssertionError("a SpatialNeuron without Im unexpectedly constructed")

    bad_point_eqs = """
    Im = 0 * amp/meter**2 : amp/meter**2
    Ibad : meter (point current)
    """
    try:
        SpatialNeuron(morphology=Soma(diameter=10 * um), model=bad_point_eqs)
    except DimensionMismatchError:
        pass
    else:
        raise AssertionError("a non-amp point current unexpectedly constructed")

    if args.constructor_only:
        print("constructor-only smoke passed: morphology, Im, Cm, Ri, and geometry")
        return 0

    try:
        import scipy  # noqa: F401 - NumPy spatial diffusion dependency
    except ImportError:
        print(
            "SciPy is required for the NumPy-target spatial run; "
            "use --constructor-only for the dependency-free check.",
            file=sys.stderr,
        )
        return 2

    monitor = StateMonitor(neuron, "v", record=[soma_index, distal_index])
    run(args.duration_ms * ms)

    if monitor.v.shape[0] != 2 or monitor.v.shape[1] == 0:
        raise AssertionError(f"unexpected monitor shape: {monitor.v.shape}")

    print(
        "ok "
        f"duration={args.duration_ms:g}ms "
        f"samples={monitor.v.shape[1]} "
        f"soma_final={monitor.v[0, -1] / mV:g}mV "
        f"distal_final={monitor.v[1, -1] / mV:g}mV"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
