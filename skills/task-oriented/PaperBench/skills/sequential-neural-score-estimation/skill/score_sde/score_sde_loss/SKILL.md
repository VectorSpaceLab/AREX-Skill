---
name: score_sde_loss
description: Construct continuous-time denoising score matching losses and tiny optimizer-step checks for Score SDE recovery.
---

# Score SDE Loss

Use this skill when training or validating a time-conditioned score model for SDE-perturbed data. It is appropriate for reduced recovery experiments that must prove the denoising score matching mechanism ran.

## Inputs

- Clean numeric batch.
- SDE marginal mean/std provider.
- Score model parameters for a simple callable or an external score function.
- Time and Gaussian noise samples.
- Learning rate for a reduced optimizer step.

## Outputs

- Perturbed data and target score.
- Scalar loss before and after update.
- Parameters before and after update.
- Boolean evidence for optimizer execution.

## Workflow

1. Use an SDE marginal to perturb data at continuous time `t`.
2. Build target score `-noise / std`.
3. Evaluate squared score residuals.
4. For reduced recovery, run a gradient step on a tiny linear score model.
5. Save loss and parameter traces with `params_before` and `params_after`.

## Validation

Run:

```bash
python tests/test_score_loss.py
python scripts/score_loss.py --data -1 -0.5 0.5 1 --t 0.4 --noise 0.2 -0.1 0.1 -0.2
```

## Limitations

The included optimizer is a deterministic reduced proxy for mechanism validation. It does not replace full neural image-model training.
