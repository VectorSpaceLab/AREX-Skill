#!/usr/bin/env python3
"""Report OpenMM imports, platforms, and bounded CPU/CUDA probes."""
from __future__ import annotations

import argparse
import importlib
import sys


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-smoke", action="store_true", help="create a tiny CPU context and take one step")
    parser.add_argument("--try-cuda", action="store_true", help="attempt a CUDA context; failure is reported as optional")
    return parser


def _platform_names(openmm) -> list[str]:
    return [openmm.Platform.getPlatform(i).getName() for i in range(openmm.Platform.getNumPlatforms())]


def _cpu_smoke(openmm, unit) -> None:
    system = openmm.System()
    system.addParticle(12.0 * unit.dalton)
    integrator = openmm.VerletIntegrator(1.0 * unit.femtoseconds)
    platform = openmm.Platform.getPlatformByName("CPU")
    context = openmm.Context(system, integrator, platform)
    context.setPositions([openmm.Vec3(0, 0, 0)] * unit.nanometer)
    integrator.step(1)
    context.getState(getEnergy=True)
    del context, integrator


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        openmm = importlib.import_module("openmm")
        unit = importlib.import_module("openmm.unit")
        app = importlib.import_module("openmm.app")
    except Exception as exc:  # pragma: no cover - depends on environment
        print(f"ERROR: OpenMM import failed: {exc}", file=sys.stderr)
        return 2
    version = getattr(openmm, "__version__", "unknown")
    print(f"OpenMM version: {version}")
    print(f"OpenMM app import: {app.__name__}")
    names = _platform_names(openmm)
    print("Platforms: " + (", ".join(names) if names else "none"))
    if "CPU" not in names:
        print("ERROR: required CPU platform is unavailable", file=sys.stderr)
        return 3
    if args.cpu_smoke:
        try:
            _cpu_smoke(openmm, unit)
            print("CPU smoke: PASS")
        except Exception as exc:
            print(f"ERROR: CPU smoke failed: {exc}", file=sys.stderr)
            return 4
    if args.try_cuda:
        if "CUDA" not in names:
            print("CUDA probe: SKIP (platform not listed)")
        else:
            try:
                platform = openmm.Platform.getPlatformByName("CUDA")
                system = openmm.System()
                system.addParticle(12.0 * unit.dalton)
                integrator = openmm.VerletIntegrator(1.0 * unit.femtoseconds)
                context = openmm.Context(system, integrator, platform)
                del context, integrator
                print("CUDA probe: PASS")
            except Exception as exc:
                print(f"CUDA probe: OPTIONAL-FAIL ({exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
