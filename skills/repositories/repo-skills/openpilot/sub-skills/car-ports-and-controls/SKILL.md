---
name: car-ports-and-controls
description: "Guides openpilot car ports, fingerprints, opendbc interfaces,
  controls tests, process replay, safety boundaries, and maneuver reports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# car-ports-and-controls

Use this sub-skill for new/changed car support, CAN/FW fingerprints, opendbc platform/interface behavior, DBC-related debugging, supported-cars docs, controller tests, driver-monitoring/control policies, process replay, and lateral/longitudinal maneuver report analysis.

## Read first

- [references/car-porting-workflows.md](references/car-porting-workflows.md) for car-port utilities, fingerprints, docs generation, and test selection.
- [references/controls-and-safety.md](references/controls-and-safety.md) for openpilot ACC/ALC/LDW/FCW/DM boundaries, controller tests, state-machine and driver-monitoring guidance.
- [references/process-replay.md](references/process-replay.md) before running process replay or generating new logs from route data.
- [references/maneuver-reports.md](references/maneuver-reports.md) before collecting or interpreting lateral/longitudinal maneuver reports.
- [references/troubleshooting.md](references/troubleshooting.md) for missing signals, fingerprint ambiguity, panda safety mismatches, process replay downloads, and unsafe Params writes.

## Bundled helper

- [scripts/extract_fingerprint_summary.py](scripts/extract_fingerprint_summary.py) adapts the route fingerprint workflow into a safer helper that reads a route/local log through `LogReader`, prints CAN address lengths, FW versions, and VIN, and never requires live Panda hardware.

## Typical workflow

1. Start with route evidence: use [route-log-analysis](../route-log-analysis/SKILL.md) to normalize route selectors and confirm logs are accessible.
2. Extract a fingerprint/FW summary when a route is available.
3. Map the platform/brand through opendbc and inspect whether firmware matching is unique or ambiguous.
4. Run focused interface/docs/controller tests; do not run all cars or process replay unless time and dependencies allow.
5. For route-based regressions, use process replay with explicit whitelist/blacklist choices.
6. For real-world maneuver data, enforce safety prerequisites and document route/upload status before report generation.

## Safety boundary

openpilot is a driver assistance system, not an autonomous replacement for driver attention. Do not suggest disabling driver monitoring, nerfing excessive actuation checks, or bypassing panda safety tests. Any fork that changes safety code must preserve the relevant safety test suite and should not claim upstream safety compliance without evidence.
