---
name: lpips_recovery_harness
description: Run a bounded source-safe LPIPS-style recovery experiment and emit validation-compatible recovery artifacts.
---

# LPIPS Recovery Harness

Use this skill after the LPIPS distance, BAPPS 2AFC protocol, and linear calibration skills exist and validate. It coordinates a soft-mode reduced recovery without reading the original source repository.

## Inputs

- Attempt directory.
- Generated skills root.
- `module_plan.json` with the fast recovery target.
- `environment/runtime_handoff.json`.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/experiment_command_log.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- `recovery/source_manifest.json`.

## Workflow

1. Read the module plan and runtime handoff.
2. Declare the strongest feasible target: full BAPPS/pretrained LPIPS if runtime is ready, otherwise soft-mode synthetic BAPPS-style proxy.
3. Construct deterministic reference and distorted patches.
4. Invoke generated LPIPS distance logic to compute per-layer contributions.
5. Invoke the calibration skill for a bounded update.
6. Invoke the 2AFC protocol skill to score calibrated distances.
7. Write mechanism checks, command logs, source manifest, and recovery result.
8. Run the Distiller recovery experiment validator.

## Validation

Run this skill from the attempt directory with:

```bash
python scripts/run_lpips_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>
```

## Limitations

The bundled harness creates a reduced proxy dataset unless the caller extends it with real BAPPS/pretrained assets. It must not be reported as full Table 5 reproduction.
