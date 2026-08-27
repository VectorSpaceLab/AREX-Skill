---
name: customization-and-analysis
description: "Extend OpenCDA localization, perception, behavior, and control
  modules while preserving runtime contracts, and analyze KF/EKF output with
  safe diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Customization and Analysis

Use this sub-skill when an OpenCDA module must be subclassed or replaced, or
when localization filters and their debug output need to be inspected. Keep
custom modules under the package's public `opencda/customize/...` convention
where possible, preserve the contracts in [references/extension-contracts.md](references/extension-contracts.md),
and wire the replacement explicitly; localization, perception, and behavior
are not discovered from YAML by the stock `VehicleManager`.

## Route the work

1. Identify one seam: `LocalizationManager`, `PerceptionManager`,
   `BehaviorAgent`, or the controller object selected by `ControlManager`.
2. Read [references/extension-contracts.md](references/extension-contracts.md)
   before changing a signature or an object shape.
3. For a KF/EKF change or numerical investigation, use
   [filter-and-debugging.md](filter-and-debugging.md). Prefer a bounded,
   non-interactive diagnostic over starting a simulator.
4. If an import, YAML selection, or plotting operation fails, follow
   [references/troubleshooting.md](references/troubleshooting.md).
5. Validate with the native KF/EKF and debug-helper tests when available, then
   run a synthetic seam check that exercises the changed input/output contract.
   Do not claim live-simulation validation unless a CARLA server was actually
   available.

## Non-negotiable limits

The inspected environment proved Python 3.8, OpenCDA 0.1.3 imports, the CARLA
0.9.12 client import, numerical/plotting dependencies, and core manager imports.
It did not prove a live CARLA server, SUMO, ScenarioRunner, torch, or YOLOv5.
Sensor spawning, ML perception, and co-simulation therefore remain external
backend gates rather than local guarantees. Keep diagnostics headless and do
not require those backends for filter-only checks.
