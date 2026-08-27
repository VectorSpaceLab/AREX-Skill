#!/usr/bin/env python3
"""Minimal OpenMM application-layer smoke test with no external input files.

This constructs a one-particle System, runs a bounded Reference-platform
Simulation, exercises reporters and portable XML state restart, and asserts
basic invariants. It is intended for quick environment validation, not physics.
"""

from __future__ import annotations

from io import StringIO
import math
import tempfile

from openmm import Platform, System, Vec3, VerletIntegrator
from openmm.app import CheckpointReporter, Simulation, StateDataReporter, Topology, element
from openmm.unit import dalton, kelvin, kilojoules_per_mole, nanometer, picoseconds


def build_one_particle_simulation() -> Simulation:
    topology = Topology()
    chain = topology.addChain("A")
    residue = topology.addResidue("MOL", chain)
    topology.addAtom("Ar", element.argon, residue)

    system = System()
    system.addParticle(39.9 * dalton)

    integrator = VerletIntegrator(0.001 * picoseconds)
    platform = Platform.getPlatformByName("Reference")
    simulation = Simulation(topology, system, integrator, platform)
    simulation.context.setPositions([Vec3(0.0, 0.0, 0.0)] * nanometer)
    simulation.context.setVelocitiesToTemperature(300 * kelvin)
    return simulation


def main() -> None:
    simulation = build_one_particle_simulation()

    log = StringIO()
    simulation.reporters.append(StateDataReporter(log, 1, step=True, time=True, kineticEnergy=True, temperature=True))

    with tempfile.TemporaryDirectory() as tempdir:
        state_path = f"{tempdir}/state.xml"
        simulation.reporters.append(CheckpointReporter(state_path, 1, writeState=True))
        simulation.step(2)

        assert simulation.currentStep == 2, f"expected step 2, got {simulation.currentStep}"
        state = simulation.context.getState(positions=True, velocities=True, energy=True)
        assert len(state.getPositions()) == 1
        assert len(state.getVelocities()) == 1
        saved_x = state.getPositions()[0].x
        kinetic = state.getKineticEnergy()
        assert math.isfinite(kinetic.value_in_unit(kilojoules_per_mole))
        assert "Step" in log.getvalue()

        simulation.context.setPositions([Vec3(1.0, 0.0, 0.0)] * nanometer)
        simulation.loadState(state_path)
        restored = simulation.context.getState(positions=True)
        restored_x = restored.getPositions()[0].x
        assert abs(restored_x - saved_x) < 1e-12, f"state restore failed, x={restored_x}, expected {saved_x}"

    print("OpenMM minimal Reference Simulation smoke passed")


if __name__ == "__main__":
    main()
