---
name: reduced_recovery_protocol
description: Build and validate soft-mode reduced recovery artifacts for residual EBM text generation without reading the original repository.
---

# Reduced Recovery Protocol

Use this skill when full residual EBM reproduction is blocked and the run is explicitly in soft mode. The skill defines the artifact contract for a reduced experiment that still exercises fixed-LM proposals, residual energy scoring, conditional NCE optimization, and importance reweighting.

Do not use this skill in hard mode as acceptance evidence. Do not read the original source repository during recovery.

## Inputs

- Attempt directory.
- Runtime handoff with full-runtime blockers and allowed sources.
- Module plan and generated skill paths.
- A reduced data item containing prefix, positive continuation, and fixed-LM-style negatives.

## Outputs

- Experiment plan explaining full and reduced targets.
- Executable recovery command.
- Source manifest with forbidden-source checks.
- Recovery result with numeric proxy metric and mechanism checks.
- Training trace with `params_before`, `params_after`, `loss_before`, and `loss_after`.
- Generated-skill invocation evidence.

## Workflow

1. Confirm recovery mode is soft and the full target is blocked by runtime or data constraints.
2. Write the experiment plan before running the experiment.
3. Build a data item from allowed paper/runtime sources, not from the original repository.
4. Invoke the generated residual scoring, NCE training, and importance sampling skills.
5. Save command logs and source manifest.
6. Run the Distiller recovery experiment validator.
7. Treat the proxy as acceptable only if mechanism checks and validation pass.

## Validation

Run:

```bash
python scripts/check_recovery_artifacts.py --attempt-dir <attempt_dir>
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/recover-paper/scripts/validate_recovery_experiment.py <attempt_dir>
```

## Limitations

This protocol proves mechanism fidelity under reduced conditions. It does not claim the CC-News or Toronto Book Corpus perplexity result unless the full model, dataset, and sample-count protocol are actually run.

