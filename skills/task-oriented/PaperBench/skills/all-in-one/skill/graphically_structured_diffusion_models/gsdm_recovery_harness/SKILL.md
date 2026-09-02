---
name: gsdm_recovery_harness
description: Run a bounded BCMF proxy recovery that exercises generated Graphically Structured Diffusion Model skills.
---

# GSDM Recovery Harness

Use this skill during soft-mode recovery for Graphically Structured Diffusion Models when full paper-scale training is blocked by wall-clock or GPU cost. It assembles the generated graph, permutation, and objective skills into one executable BCMF proxy experiment.

Do not use this skill to claim full reproduction of the paper's RMSE curves. It produces mechanism-faithful reduced evidence only.

## Inputs

- `attempt_dir`: current Distiller attempt directory.
- `skill_root`: directory containing the generated GSDM skills.
- `environment/runtime_handoff.json`: runtime preflight from `prepare-recovery-environment`.
- BCMF dimensions and optimizer settings.

## Outputs

- `recovery/logs/generated_data_item.json`
- `recovery/logs/training_trace.json`
- `recovery/logs/generated_skill_invocations.json`
- `recovery/source_manifest.json`
- `recovery/recovery_result.json`

## Workflow

1. Build a deterministic tiny BCMF item.
2. Invoke the graph skill to produce the structured attention mask.
3. Invoke the permutation skill to verify a full plate-index swap preserves that mask.
4. Invoke the objective skill to encode mixed continuous/binary variables and compute the masked denoising loss.
5. Run a scalar denoiser optimizer step against the masked `x0` objective.
6. Write source-boundary, command, and mechanism-check evidence.

## CLI

```bash
python scripts/run_gsdm_recovery.py --attempt-dir /path/to/attempt --skill-root /path/to/generated/skills --learning-rate 0.05
```

## Validation

```bash
python -m pytest tests
```

The tests run the scalar step in memory and assert that loss decreases and parameters change. The learning rate is exposed so refinement cycles can stress optimizer stability without editing the script.

## Limitations

The proxy uses a small scalar denoiser rather than the full transformer. It is acceptable only under soft recovery mode after the runtime handoff records full-scale blockers.
