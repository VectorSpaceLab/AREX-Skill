---
name: imagenet_c_recovery_harness
description: Run a bounded mechanism-faithful ImageNet-C proxy recovery using generated corruption and metric skills without reading the original repository.
---

# ImageNet-C Recovery Harness

Use this skill after the corruption protocol and metric skills are generated. It runs a small executable proxy experiment when full ImageNet-C data and pretrained models are unavailable, while preserving the paper's benchmark mechanism.

## Inputs

- `attempt_dir` containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing `imagenet_c_corruption_protocol`, `imagenet_c_corruption_metrics`, and `imagenet_p_perturbation_metrics`.
- Experiment controls: sample count, corruption names, severity levels, and seed.

## Outputs

- Recovery plan, source manifest, command logs, generated data item, prediction/error tables, generated skill invocation log, and `recovery_result.json`.

## Workflow

1. Read the module-plan target and runtime handoff.
2. Generate a small deterministic image classification dataset.
3. Apply representative common corruptions with the corruption protocol skill.
4. Run deterministic baseline and evaluated classifiers.
5. Compute CE, mCE, relative CE, and relative mCE with the metric skill.
6. Cross-check ImageNet-P flip probability on synthetic prediction sequences.
7. Save mechanism checks and recovery artifacts.
8. Run the Distiller recovery validator outside the harness.

## Validation

Run:

```bash
python tests/test_recovery_harness.py
```

## Limitations

The harness produces a declared soft-mode proxy. It is not a full ImageNet-C reproduction unless the runtime handoff supplies ImageNet validation data, ImageNet-C corruptions, and pretrained classifier execution.
