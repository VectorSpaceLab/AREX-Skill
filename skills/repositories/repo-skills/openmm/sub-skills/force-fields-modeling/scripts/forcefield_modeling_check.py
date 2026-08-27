#!/usr/bin/env python3
"""Lightweight OpenMM force-field/model-building smoke check.

This script is intentionally self-contained.  It builds a tiny water topology in
memory, verifies ForceField template matching, creates a System, and prints a
JSON summary.  It does not require the OpenMM source checkout or external input
files.
"""

from __future__ import annotations

import json
import sys


def build_water_topology():
    from openmm import Vec3
    from openmm.app import Element, Topology
    from openmm.unit import nanometer

    topology = Topology()
    chain = topology.addChain("A")
    residue = topology.addResidue("HOH", chain)
    oxygen = topology.addAtom("O", Element.getBySymbol("O"), residue)
    hydrogen1 = topology.addAtom("H1", Element.getBySymbol("H"), residue)
    hydrogen2 = topology.addAtom("H2", Element.getBySymbol("H"), residue)
    topology.addBond(oxygen, hydrogen1)
    topology.addBond(oxygen, hydrogen2)
    topology.setPeriodicBoxVectors(
        (
            Vec3(2.0, 0.0, 0.0),
            Vec3(0.0, 2.0, 0.0),
            Vec3(0.0, 0.0, 2.0),
        )
        * nanometer
    )
    positions = [
        Vec3(0.00000, 0.00000, 0.00000),
        Vec3(0.09572, 0.00000, 0.00000),
        Vec3(-0.02399, 0.09266, 0.00000),
    ] * nanometer
    return topology, positions


def main() -> int:
    try:
        import openmm
        from openmm.app import CutoffPeriodic, ForceField, HBonds, Modeller, PME
        from openmm.unit import nanometer

        topology, positions = build_water_topology()
        forcefield = ForceField("tip3p.xml")

        unmatched_before = forcefield.getUnmatchedResidues(topology)
        templates = forcefield.getMatchingTemplates(topology)
        system = forcefield.createSystem(
            topology,
            nonbondedMethod=CutoffPeriodic,
            nonbondedCutoff=0.9 * nanometer,
            constraints=HBonds,
            rigidWater=True,
        )

        modeller = Modeller(topology, positions)
        modeller.addExtraParticles(forcefield)
        unmatched_after_extra_particles = forcefield.getUnmatchedResidues(modeller.topology)

        summary = {
            "ok": True,
            "openmm_version": getattr(openmm, "version", None).version if hasattr(openmm, "version") else None,
            "forcefield_files": ["tip3p.xml"],
            "residue_count": sum(1 for _ in topology.residues()),
            "template_names": [template.name for template in templates],
            "unmatched_before": [residue.name for residue in unmatched_before],
            "unmatched_after_extra_particles": [residue.name for residue in unmatched_after_extra_particles],
            "particles": system.getNumParticles(),
            "forces": [system.getForce(index).__class__.__name__ for index in range(system.getNumForces())],
            "periodic_box": topology.getPeriodicBoxVectors() is not None,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - command-line diagnostic path
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                    "hint": "Install OpenMM in the active Python environment, then rerun this script.",
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
