#!/usr/bin/env python3
"""Run a checkout-independent OpenMM Reference-platform smoke test."""

import json
import math
import sys

try:
    import openmm
    from openmm import Context, Platform, System, Vec3, VerletIntegrator
    from openmm.unit import dalton, nanometer, picosecond
except Exception as exc:
    print(json.dumps({"ok": False, "phase": "import", "error": str(exc)}))
    sys.exit(1)


def main() -> int:
    platforms = [Platform.getPlatform(index).getName() for index in range(Platform.getNumPlatforms())]
    platform = Platform.getPlatformByName("Reference")

    system = System()
    system.addParticle(39.9 * dalton)
    integrator = VerletIntegrator(0.001 * picosecond)
    context = Context(system, integrator, platform)
    context.setPositions([Vec3(0.0, 0.0, 0.0) * nanometer])
    state = context.getState(getPositions=True, getEnergy=True)
    positions = state.getPositions(asNumpy=True)
    potential_energy = state.getPotentialEnergy()

    ok = len(positions) == 1 and math.isfinite(potential_energy.value_in_unit(potential_energy.unit))
    print(json.dumps({
        "ok": ok,
        "openmm_version": getattr(openmm, "__version__", "unknown"),
        "platforms": platforms,
        "smoke_platform": platform.getName(),
        "particles": system.getNumParticles(),
    }, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
