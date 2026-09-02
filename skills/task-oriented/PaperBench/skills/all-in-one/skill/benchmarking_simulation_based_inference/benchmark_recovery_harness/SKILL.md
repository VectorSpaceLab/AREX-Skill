---
name: benchmark_recovery_harness
description: Run bounded SBI benchmark recovery from generated skills while enforcing source boundaries and validator-compatible evidence.
---

# Benchmark Recovery Harness

Use this skill after the task protocol, posterior approximation, and two-sample metric skills exist and validate. It coordinates a reduced Gaussian-linear recovery of the paper's benchmark mechanism, writes auditable Distiller artifacts, and records generated skill invocations.

Do not read the original paper repository during recovery. Use only the paper, module docs, generated skills, runtime handoff, and current-attempt snapshots or logs listed in the source manifest.

## Inputs

- `attempt_dir`
- `skill_root`
- `module_plan.json`
- `environment/runtime_handoff.json`
- Recovery parameters such as sample count, simulation count, and learning rate.

## Outputs

- Recovery plan and source manifest.
- Generated data item, training trace, skill invocation log, and recovery result.
- Numeric metric evidence and mechanism checks.
- C2ST distance-to-ideal evidence so downstream analysis can interpret classifier accuracy by closeness to `0.5`.

## Workflow

1. Write or update `recovery/experiment_plan.md`.
2. Import generated skill scripts from the skill root.
3. Build the Gaussian-linear proxy task and simulation pairs.
4. Generate analytic reference posterior samples.
5. Fit approximate posterior samples with the posterior approximation skill.
6. Compute C2ST-style metrics with the metric skill.
7. Write `recovery_result.json` using the target from `module_plan.json`.
8. Write source and invocation manifests that prove the generated skills were exercised.

## Source Boundary Invariant

Before treating a recovery as valid, search the serialized `recovery/source_manifest.json` for the original repository checkout path from the run config or source-resolution record. The manifest may mention current-attempt snapshots copied during environment preparation, but it must not list or depend on the original checkout. If the original checkout path appears, rerun recovery with only generated skills and current-attempt artifacts.

## Validation

Run:

```bash
python scripts/run_recovery.py --attempt-dir <attempt_dir> --skill-root <skill_root>
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/recover-paper/scripts/validate_recovery_experiment.py <attempt_dir> --output <attempt_dir>/recovery/experiment_validation.json
```

## Limitations

This harness implements a declared soft-mode proxy. It must not be accepted for hard-mode recovery or described as a full reproduction across all `sbibm` tasks and algorithms.
