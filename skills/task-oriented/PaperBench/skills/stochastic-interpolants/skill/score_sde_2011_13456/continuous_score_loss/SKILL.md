---
name: continuous_score_loss
description: Build continuous denoising score-matching targets and deterministic optimizer checks for score-SDE recovery.
---

# Continuous Score Loss

Use this skill when training or validating a score-SDE mechanism on perturbed data. It constructs analytical VE perturbation scores and a weighted mean-squared denoising score-matching objective. It is suitable for tiny reduced recovery and unit tests, not for claiming full image-model performance.

## Inputs
- Clean scalar samples, continuous times, and deterministic noise values.
- A schedule implementation that supplies `sigma(t)`.
- Linear score-model parameters or explicit predictions.
- Optional loss weighting mode.

## Outputs
- Perturbed samples and target scores.
- Mean score-matching loss.
- Gradients and updated parameters for a tiny linear score model.

## Workflow
1. Pair each clean sample with a time and noise value.
2. Perturb with the VE kernel and compute `target_score=-noise/sigma(t)`.
3. Predict score with `a*x_t + b*t + c` for reduced recovery.
4. Compute mean squared error and gradients.
5. Apply a bounded optimizer step and record before/after loss and parameters.

## Validation
Run `python scripts/continuous_score_loss.py --self-test` or the generated skill validator with tests enabled.

## Limitations
The included optimizer is intentionally tiny and standard-library only. It proves the denoising-score objective can execute under bounded constraints but is not a substitute for full neural network training.
