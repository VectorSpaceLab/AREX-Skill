---
name: gaussian_sbi_recovery
description: Run a bounded Gaussian/Gaussian SBI proxy recovery that exercises F-NPSE score training, composition, and sampling.
---

# Gaussian SBI Recovery Harness

Use this skill to produce executable soft-mode recovery evidence for Compositional Score Modeling for Simulation-Based Inference when the full paper benchmark suite or original implementation is unavailable. It targets the paper's Gaussian/Gaussian benchmark family because the posterior is analytic and the core mechanism can be verified cheaply.

Do not use this skill to claim full paper reproduction. It is a declared reduced/proxy recovery harness whose output must say so.

## Inputs

- Attempt directory containing `module_plan.json`.
- Runtime handoff from `prepare-recovery-environment`.
- Generated skill root containing `denoising_score_training`, `factorized_score_composition`, and `annealed_langevin_sampler`.
- Small experiment controls: seed, dimension, observation count, sample count, and Langevin settings.

## Outputs

- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/sampler_trace.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/source_manifest.json`.
- `recovery/recovery_result.json`.

## Workflow

1. Generate a Gaussian/Gaussian simulator item from a standard normal prior and diagonal Gaussian likelihood.
2. Compute the analytic multi-observation posterior.
3. Run a real denoising score optimizer step using the training skill.
4. Build analytic single-observation posterior score terms for a calibrated proxy score predictor.
5. Compose scores using the F-NPSE composition skill.
6. Sample with the annealed Langevin skill.
7. Compute squared MMD, posterior mean error, and a bounded higher-is-better proxy score.
8. Write recovery artifacts and mechanism checks for the Distiller validators.

## Validation

Run the harness and then run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/recover-paper/scripts/validate_recovery_experiment.py <attempt_dir> --output <attempt_dir>/recovery/experiment_validation.json
```

The experiment is acceptable only when the gate reports `ok: true` and the analysis report accepts the declared proxy scope.

## Limitations

The harness uses an analytic Gaussian score for the sampling path after running a reduced score-training step. This isolates the compositional mechanism and sampler under bounded runtime but does not reproduce the paper's neural network training scale, full noise schedule, or benchmark figures.
