---
name: denoising_score_training
description: Train and validate conditional denoising score models for F-NPSE or PF-NPSE simulation-based inference recoveries.
---

# Denoising Score Training

Use this skill when a recovery or implementation needs the score-matching part of Compositional Score Modeling for Simulation-Based Inference. It is appropriate for NPSE, F-NPSE, and PF-NPSE score learners that receive simulator-generated `(theta, condition)` pairs and predict the Gaussian denoising score at a selected diffusion level.

Do not use this skill to combine multiple observations or to sample from the posterior. Score composition belongs to `factorized_score_composition`; posterior sampling belongs to `annealed_langevin_sampler`.

## Inputs

- Clean simulator parameter vectors `theta_clean`.
- Conditioning values: one observation for F-NPSE, or a small observation group for PF-NPSE.
- Diffusion coefficient `gamma` with `0 < gamma < 1`.
- A parameterized score predictor. The bundled script provides a small linear conditional predictor for bounded recovery experiments.

## Outputs

- Gaussian denoising target scores.
- Mean squared denoising score loss.
- Optimizer trace with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- A predictor callable or serialized parameter dictionary usable by composition and recovery scripts.

## Workflow

1. Generate noisy parameters with `theta_t = sqrt(gamma) * theta_clean + sqrt(1 - gamma) * epsilon`.
2. Compute the target score `(sqrt(gamma) * theta_clean - theta_t) / (1 - gamma)`.
3. Evaluate the conditional score predictor on `theta_t`, `gamma`, and the condition.
4. Minimize the squared error against the target.
5. Record parameter movement and before/after loss whenever this is used as reduced recovery evidence.

## Validation

Run the deterministic test suite:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

The tests use a Gaussian fixture and verify finite denoising targets, decreasing or non-increasing loss after a small gradient step, and changed trainable parameters.

## Limitations

The bundled linear predictor is a recovery aid, not the paper's full neural architecture. A full reproduction should replace it with a neural score network while preserving the same denoising target and trace contract.
