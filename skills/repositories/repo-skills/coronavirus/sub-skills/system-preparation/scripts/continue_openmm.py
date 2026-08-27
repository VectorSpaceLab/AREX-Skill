#!/usr/bin/env python3
"""Run a bounded continuation from matching OpenMM XML artifacts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-pdb", required=True, type=Path, help="equilibrated PDB supplying topology and coordinates")
    parser.add_argument("--system-xml", required=True, type=Path)
    parser.add_argument("--state-xml", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--timestep-fs", type=float, default=4.0)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    parser.add_argument("--collision-rate-per-ps", type=float, default=91.0)
    parser.add_argument("--splitting", default="V R O R V")
    parser.add_argument("--platform", choices=("CPU", "CUDA", "Reference"), default="CPU")
    parser.add_argument("--allow-long-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    for label, path in (("input PDB", args.input_pdb), ("system XML", args.system_xml), ("state XML", args.state_xml)):
        if not path.is_file():
            return _fail(f"{label} does not exist: {path}")
    if min(args.steps, args.iterations, args.timestep_fs, args.temperature_k, args.collision_rate_per_ps) <= 0:
        return _fail("steps, iterations, timestep, temperature, and collision rate must be positive")
    total_steps = args.steps * args.iterations
    if total_steps > 100_000 and not args.allow_long_run:
        return _fail(f"refusing {total_steps} steps; use a reviewed --allow-long-run command")
    try:
        import openmm
        from openmm import app, unit
    except Exception as exc:
        return _fail(f"OpenMM import failed: {exc}")
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    names = ("continued.pdb", "system.xml", "integrator.xml", "state.xml")
    existing = [name for name in names if (output / name).exists()]
    if existing and not args.overwrite:
        return _fail(f"output already contains {', '.join(existing)}; choose a new directory or pass --overwrite")
    try:
        pdb = app.PDBFile(str(args.input_pdb))
        system = openmm.XmlSerializer.deserialize(args.system_xml.read_text())
        state = openmm.XmlSerializer.deserialize(args.state_xml.read_text())
        if not isinstance(system, openmm.System):
            return _fail("system XML does not deserialize to an OpenMM System")
        if not isinstance(state, openmm.State):
            return _fail("state XML does not deserialize to an OpenMM State")
        if system.getNumParticles() != pdb.topology.getNumAtoms():
            return _fail(f"PDB has {pdb.topology.getNumAtoms()} atoms but system has {system.getNumParticles()}")
        integrator = openmm.LangevinMiddleIntegrator(
            args.temperature_k * unit.kelvin,
            args.collision_rate_per_ps / unit.picosecond,
            args.timestep_fs * unit.femtosecond,
        )
        # LangevinMiddleIntegrator has no splitting parameter. The requested
        # splitting is retained in the report; use LangevinIntegrator when a
        # non-default splitting is explicitly needed.
        if args.splitting != "V R O R V":
            del integrator
            integrator = openmm.LangevinIntegrator(
                args.temperature_k * unit.kelvin,
                args.collision_rate_per_ps / unit.picosecond,
                args.timestep_fs * unit.femtosecond,
                args.splitting,
            )
        platform = openmm.Platform.getPlatformByName(args.platform)
        context = openmm.Context(system, integrator, platform)
        context.setState(state)
        for _ in range(args.iterations):
            integrator.step(args.steps)
        final_state = context.getState(getPositions=True, getVelocities=True, getEnergy=True, getForces=True)
        with (output / "continued.pdb").open("w") as handle:
            app.PDBFile.writeFile(pdb.topology, final_state.getPositions(), handle, keepIds=True)
        (output / "integrator.xml").write_text(openmm.XmlSerializer.serialize(integrator))
        (output / "state.xml").write_text(openmm.XmlSerializer.serialize(final_state))
        system.setDefaultPeriodicBoxVectors(*final_state.getPeriodicBoxVectors())
        (output / "system.xml").write_text(openmm.XmlSerializer.serialize(system))
        print(f"Wrote {len(names)} files to {output}; steps={total_steps}; timestep_fs={args.timestep_fs}; splitting={args.splitting}")
        return 0
    except Exception as exc:
        return _fail(f"OpenMM continuation failed: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
