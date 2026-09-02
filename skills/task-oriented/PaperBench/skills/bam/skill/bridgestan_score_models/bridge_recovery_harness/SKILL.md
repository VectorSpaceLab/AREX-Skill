---
name: bridge_recovery_harness
description: Run a bounded BridgeStan score-model proxy recovery that invokes generated module scripts, logs command evidence, and writes validator-ready recovery artifacts.
---

# Bridge Recovery Harness

Use this skill when a soft-mode recovery must prove BridgeStan-like score-model behavior without compiling the full BridgeStan stack. It coordinates the other generated skills and produces auditable recovery artifacts.

## Inputs
- Attempt directory.
- Generated skills root.
- `module_plan.json` fast recovery target.
- `environment/runtime_handoff.json`.

## Outputs
- `recovery/recovery_result.json`.
- `recovery/source_manifest.json`.
- `recovery/logs/experiment_command_log.json`.
- `recovery/logs/generated_skill_invocations.json`.
- Data, contract, transform, and score logs used by the proxy.

## Workflow
1. Confirm the runtime handoff recommends reduced/proxy recovery or that full BridgeStan runtime is unavailable.
2. Create a tiny Bernoulli Stan source and observation data inside the current attempt.
3. Call the generated contract, transform, and score scripts through subprocesses.
4. Compute a mechanism-check pass-rate metric from the generated outputs.
5. Write source manifest entries limited to allowed recovery sources.
6. Run the Distiller recovery validator after the harness completes.

## Validation
Run `python tests/test_bridge_recovery_harness.py` from this skill directory for a command-free smoke check of metric aggregation.

## Limitations
This harness is a declared proxy. It must not claim that the real BridgeStan package or compiled Stan shared object ran unless environment evidence proves that separately.
