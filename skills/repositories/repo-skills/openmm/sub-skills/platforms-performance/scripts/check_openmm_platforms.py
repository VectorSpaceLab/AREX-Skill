#!/usr/bin/env python3
"""List and lightly smoke-test installed OpenMM platforms.

This diagnostic is adapted from OpenMM's installation-test pattern but keeps the
system tiny so it is safe for routine troubleshooting. It does not benchmark
performance and it does not require files from an OpenMM source checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Dict, Iterable, List, Optional


def _import_openmm():
    try:
        import openmm as mm
        import openmm.unit as unit
    except Exception as exc:  # pragma: no cover - exercised by broken envs
        print("ERROR: failed to import openmm", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return None, None
    return mm, unit


def _platforms(mm) -> List[object]:
    return [mm.Platform.getPlatform(index) for index in range(mm.Platform.getNumPlatforms())]


def _properties_for_platform(platform_name: str, precision: Optional[str], device_index: Optional[str], threads: Optional[str]) -> Dict[str, str]:
    properties: Dict[str, str] = {}
    if platform_name in {"CUDA", "OpenCL", "HIP"} and precision:
        properties["Precision"] = precision
    if platform_name in {"CUDA", "OpenCL", "HIP"} and device_index:
        properties["DeviceIndex"] = device_index
    if platform_name == "CPU" and threads:
        properties["Threads"] = threads
    return properties


def _make_tiny_system(mm, unit):
    system = mm.System()
    system.addParticle(39.9 * unit.amu)
    system.addParticle(39.9 * unit.amu)
    force = mm.HarmonicBondForce()
    force.addBond(0, 1, 0.3 * unit.nanometer, 100.0 * unit.kilojoule_per_mole / unit.nanometer**2)
    system.addForce(force)
    positions = [
        mm.Vec3(0.0, 0.0, 0.0),
        mm.Vec3(0.31, 0.0, 0.0),
    ] * unit.nanometer
    integrator = mm.VerletIntegrator(0.001 * unit.picoseconds)
    return system, integrator, positions


def _smoke_platform(mm, unit, platform, args) -> Dict[str, object]:
    name = platform.getName()
    properties = _properties_for_platform(name, args.precision, args.device_index, args.threads)
    result: Dict[str, object] = {
        "name": name,
        "properties": properties,
        "ok": False,
    }
    try:
        system, integrator, positions = _make_tiny_system(mm, unit)
        context = mm.Context(system, integrator, platform, properties)
        context.setPositions(positions)
        state = context.getState(getEnergy=True)
        energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        result.update({"ok": True, "potential_energy_kj_per_mol": energy})
        del context
    except Exception as exc:  # pragma: no cover - depends on host backends
        result.update({
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        })
        if args.traceback:
            result["traceback"] = traceback.format_exc()
    finally:
        try:
            del integrator
        except UnboundLocalError:
            pass
    return result


def _select_platforms(platforms: Iterable[object], requested: Optional[List[str]]) -> List[object]:
    platforms = list(platforms)
    if not requested:
        return platforms
    by_name = {platform.getName(): platform for platform in platforms}
    selected = []
    missing = []
    for name in requested:
        if name in by_name:
            selected.append(by_name[name])
        else:
            missing.append(name)
    if missing:
        available = ", ".join(sorted(by_name)) or "none"
        raise SystemExit(f"Requested platform(s) not available: {', '.join(missing)}. Available: {available}")
    return selected


def _print_text(version: str, platform_names: List[str], smoke_results: Optional[List[Dict[str, object]]]) -> None:
    print(f"OpenMM version: {version}")
    print(f"Available platforms ({len(platform_names)}): {', '.join(platform_names) if platform_names else 'none'}")
    if smoke_results is None:
        return
    print("\nSmoke results:")
    for result in smoke_results:
        name = result["name"]
        if result["ok"]:
            energy = result["potential_energy_kj_per_mol"]
            print(f"- {name}: ok, potential_energy={energy:.8g} kJ/mol, properties={result['properties']}")
        else:
            print(f"- {name}: FAILED ({result.get('error_type', 'Error')}): {result.get('error', '')}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="List and lightly smoke-test installed OpenMM platforms.")
    parser.add_argument("--list", action="store_true", help="List available platforms. This is the default when --smoke is omitted.")
    parser.add_argument("--smoke", action="store_true", help="Create a tiny Context and compute an energy on selected platforms.")
    parser.add_argument("--platform", action="append", help="Platform name to smoke-test. May be repeated. Defaults to all available platforms.")
    parser.add_argument("--precision", choices=["single", "mixed", "double"], default=None, help="Precision property for CUDA/OpenCL/HIP smoke tests.")
    parser.add_argument("--device-index", default=None, help="DeviceIndex property for CUDA/OpenCL/HIP smoke tests, such as 0 or 0,1.")
    parser.add_argument("--threads", default=None, help="Threads property for CPU smoke tests.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--traceback", action="store_true", help="Include Python tracebacks in JSON smoke failures.")
    args = parser.parse_args(argv)

    mm, unit = _import_openmm()
    if mm is None:
        return 1

    platforms = _platforms(mm)
    platform_names = [platform.getName() for platform in platforms]
    smoke_results = None
    exit_code = 0

    if args.smoke:
        selected = _select_platforms(platforms, args.platform)
        smoke_results = [_smoke_platform(mm, unit, platform, args) for platform in selected]
        if any(not result["ok"] for result in smoke_results):
            exit_code = 2

    if args.json:
        payload = {
            "openmm_version": mm.Platform.getOpenMMVersion(),
            "platforms": platform_names,
            "smoke_results": smoke_results,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(mm.Platform.getOpenMMVersion(), platform_names, smoke_results)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
