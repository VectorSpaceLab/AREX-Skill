#!/usr/bin/env python3
"""Prepare a bounded, generic solvated OpenMM protein system."""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-pdb", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--steps", type=int, default=10, help="integration steps per iteration (default: 10)")
    parser.add_argument("--iterations", type=int, default=1, help="number of step batches (default: 1)")
    parser.add_argument("--temperature-k", type=float, default=310.0)
    parser.add_argument("--padding-angstrom", type=float, default=10.0)
    parser.add_argument("--ionic-strength-molar", type=float, default=0.15)
    parser.add_argument("--hydrogen-mass-amu", type=float, default=4.0)
    parser.add_argument("--timestep-fs", type=float, default=2.0)
    parser.add_argument("--platform", choices=("CPU", "CUDA", "Reference"), default="CPU")
    parser.add_argument("--allow-long-run", action="store_true", help="allow more than the safe bounded step budget")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing files in an existing output directory")
    return parser


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.input_pdb.is_file():
        return _fail(f"input PDB does not exist: {args.input_pdb}")
    if min(args.steps, args.iterations) < 1:
        return _fail("--steps and --iterations must be positive")
    if min(args.temperature_k, args.padding_angstrom, args.ionic_strength_molar, args.hydrogen_mass_amu, args.timestep_fs) <= 0:
        return _fail("physical numeric options must be positive")
    total_steps = args.steps * args.iterations
    if total_steps > 100_000 and not args.allow_long_run:
        return _fail(f"refusing {total_steps} steps; use a reviewed --allow-long-run command")
    try:
        from openmm import LangevinIntegrator, MonteCarloBarostat, Platform, XmlSerializer, app, unit
    except Exception as exc:
        return _fail(f"OpenMM import failed: {exc}")
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    names = ("solvated.pdb", "minimized.pdb", "equilibrated.pdb", "system.xml", "integrator.xml", "state.xml")
    existing = [name for name in names if (output / name).exists()]
    if existing and not args.overwrite:
        return _fail(f"output already contains {', '.join(existing)}; choose a new directory or pass --overwrite")
    try:
        pdb = app.PDBFile(str(args.input_pdb))
        forcefield = app.ForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
        modeller = app.Modeller(pdb.topology, pdb.positions)
        modeller.addSolvent(
            forcefield,
            model="tip3p",
            padding=args.padding_angstrom * unit.angstrom,
            ionicStrength=args.ionic_strength_molar * unit.molar,
        )
        with (output / "solvated.pdb").open("w") as handle:
            app.PDBFile.writeFile(modeller.topology, modeller.positions, handle, keepIds=True)
        system = forcefield.createSystem(
            modeller.topology,
            nonbondedMethod=app.PME,
            constraints=app.HBonds,
            removeCMMotion=False,
            hydrogenMass=args.hydrogen_mass_amu * unit.amu,
        )
        temperature = args.temperature_k * unit.kelvin
        system.addForce(MonteCarloBarostat(1.0 * unit.atmosphere, temperature))
        integrator = LangevinIntegrator(temperature, 91.0 / unit.picosecond, args.timestep_fs * unit.femtosecond)
        platform = Platform.getPlatformByName(args.platform)
        context = __import__("openmm").Context(system, integrator, platform)
        context.setPositions(modeller.positions)
        __import__("openmm").LocalEnergyMinimizer.minimize(context)
        with (output / "minimized.pdb").open("w") as handle:
            app.PDBFile.writeFile(modeller.topology, context.getState(getPositions=True, enforcePeriodicBox=True).getPositions(), handle, keepIds=True)
        started = time.monotonic()
        for _ in range(args.iterations):
            integrator.step(args.steps)
        elapsed = time.monotonic() - started
        state = context.getState(getPositions=True, getVelocities=True, getEnergy=True, getForces=True)
        with (output / "equilibrated.pdb").open("w") as handle:
            app.PDBFile.writeFile(modeller.topology, state.getPositions(asNumpy=False), handle, keepIds=True)
        (output / "integrator.xml").write_text(XmlSerializer.serialize(integrator))
        (output / "state.xml").write_text(XmlSerializer.serialize(state))
        system.setDefaultPeriodicBoxVectors(*state.getPeriodicBoxVectors())
        (output / "system.xml").write_text(XmlSerializer.serialize(system))
        print(f"Wrote {len(names)} files to {output}; atoms={modeller.topology.getNumAtoms()}; elapsed={elapsed:.3f}s")
        return 0
    except Exception as exc:
        return _fail(f"OpenMM preparation failed: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
