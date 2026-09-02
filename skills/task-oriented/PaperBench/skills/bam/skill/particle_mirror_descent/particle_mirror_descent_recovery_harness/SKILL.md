---
name: particle_mirror_descent_recovery_harness
description: Use this skill to compose PMD mixture protocol, KDE update, and density metrics modules into an executable bounded soft-mode recovery experiment with auditable evidence.
---

# Reduced PMD Recovery Harness

## When To Use

Use this skill for a bounded recovery of the Particle Mirror Descent synthetic mixture result when full large-scale comparisons are infeasible. Do not use it as evidence unless the harness invokes the generated protocol, update, and metric skills.

## Inputs

- Attempt directory containing `module_plan.json`, `run_manifest.json`, and `environment/runtime_handoff.json`.
- Generated skill root with the three core PMD module skills.
- Experiment parameters: seed, observation count, particles per mode, iterations, batch size, step size, and mode radius.

## Outputs

- `recovery/recovery_result.json` with metrics and mechanism checks.
- `recovery/source_manifest.json` proving no original repository usage.
- `recovery/logs/generated_data_item.json`, `training_trace.json`, and `generated_skill_invocations.json`.

## Workflow

1. Load the module plan target from the current attempt.
2. Import generated skill scripts by path rather than using any original repository.
3. Generate the reduced tied Gaussian mixture data item.
4. Initialize particles near both symmetric modes plus diffuse prior particles.
5. Run PMD KDE updates and score symmetric mode coverage.
6. Write all recovery artifacts from the executable command.

## Validation

Run the attempt-level recovery command followed by `recover-paper/scripts/validate_recovery_experiment.py`.

## Limitations

This is a declared soft-mode proxy. It validates mechanism fidelity, not the full paper's repeated baseline comparison or final figure reproduction.
