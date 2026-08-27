#!/usr/bin/env python3
"""Smoke test for OpenMM custom force support on the Reference platform."""

import math

import openmm
from openmm import unit


def main() -> None:
    system = openmm.System()
    system.addParticle(39.9 * unit.amu)
    system.addParticle(39.9 * unit.amu)

    force = openmm.CustomBondForce("0.5*k*(r-r0)^2")
    force.addGlobalParameter("k", 100.0 * unit.kilojoule_per_mole / unit.nanometer**2)
    force.addPerBondParameter("r0")
    force.addBond(0, 1, [0.25 * unit.nanometer])
    system.addForce(force)

    integrator = openmm.VerletIntegrator(1.0 * unit.femtosecond)
    platform = openmm.Platform.getPlatformByName("Reference")
    context = openmm.Context(system, integrator, platform)
    context.setPositions([
        openmm.Vec3(0.0, 0.0, 0.0) * unit.nanometer,
        openmm.Vec3(0.30, 0.0, 0.0) * unit.nanometer,
    ])

    state = context.getState(getEnergy=True, getForces=True)
    energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    forces = state.getForces(asNumpy=False)
    force_norm = math.sqrt(sum(
        component.value_in_unit(unit.kilojoule_per_mole / unit.nanometer) ** 2
        for vector in forces
        for component in vector
    ))

    assert math.isfinite(energy), f"non-finite custom force energy: {energy}"
    assert energy > 0.0, f"expected positive restraint energy, got {energy}"
    assert math.isfinite(force_norm) and force_norm > 0.0, f"bad force norm: {force_norm}"
    print(f"custom force smoke passed: energy={energy:.6g} kJ/mol, force_norm={force_norm:.6g} kJ/(mol*nm)")


if __name__ == "__main__":
    main()
