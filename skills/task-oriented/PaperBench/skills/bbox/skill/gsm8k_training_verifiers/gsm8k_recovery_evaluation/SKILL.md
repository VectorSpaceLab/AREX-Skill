---
name: gsm8k_recovery_evaluation
description: Run a bounded GSM8K verifier recovery harness with source provenance, generated-skill invocation logs, and solve-rate metrics.
---

# GSM8K Recovery Evaluation

Use this skill to run the soft-mode recovery experiment for the GSM8K verifier paper. It orchestrates the generated answer, candidate, verifier-training, and verifier-search skills and emits validator-compatible recovery artifacts.

Do not run this skill against the original repository during recovery. Use only the runtime handoff's allowed current-attempt snapshot files.

## Inputs

- Attempt directory with `module_plan.json`.
- Runtime handoff with allowed snapshot paths.
- Generated skills root.

## Outputs

- Recovery result with numeric `solve_rate`.
- Generated data item and training trace.
- Command and generated-skill invocation logs.
- Source manifest that excludes the original repository.

## Workflow

1. Read `environment/runtime_handoff.json`.
2. Resolve the allowed GSM8K snapshot file.
3. Generate reduced candidate records.
4. Train the lightweight verifier and save loss/parameter trace.
5. Rank candidates and produce predictions.
6. Evaluate solve rate.
7. Write mechanism checks and provenance artifacts.

## Validation

Run the harness and then the Distiller recovery validator:

```bash
python scripts/run_recovery.py --attempt-dir /path/to/attempt --skills-root /path/to/generated_skills
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/recover-paper/scripts/validate_recovery_experiment.py /path/to/attempt --output /path/to/attempt/recovery/experiment_validation.json
```

## Limitations

This harness is a reduced proxy when full model checkpoints and GPT-3-family training infrastructure are unavailable. It must keep full-model booleans false and explicitly record reduced training as the accepted soft-mode scope.
