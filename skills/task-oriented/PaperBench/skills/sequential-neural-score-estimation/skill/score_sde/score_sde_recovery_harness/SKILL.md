---
name: score_sde_recovery_harness
description: Execute a bounded soft-mode Score SDE recovery experiment using generated skills and mechanism checks.
---

# Score SDE Recovery Harness

Use this skill after module skills and runtime handoff exist. It assembles the generated SDE, loss, sampler, and probability-flow skills into an executable reduced experiment without reading the original repository.

## Inputs

- Attempt directory.
- Generated skills root.
- Runtime handoff path.
- Module plan target.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/source_manifest.json`.

## Workflow

1. Read the module plan and runtime handoff.
2. Construct a deterministic tiny synthetic batch.
3. Import or call every generated core skill.
4. Run one denoising score matching optimizer update.
5. Run PC sampler and probability-flow diagnostics.
6. Write all recovery artifacts and mechanism checks.
7. Run the Distiller recovery experiment validator.

## Validation

Run:

```bash
python tests/test_recovery_harness.py
python scripts/run_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>
```

## Limitations

This is a declared soft-mode proxy. It must not be reported as full CIFAR-10 FID, Inception Score, or bits/dim reproduction.
