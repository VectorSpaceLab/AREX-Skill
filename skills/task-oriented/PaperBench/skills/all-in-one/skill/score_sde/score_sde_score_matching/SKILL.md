---
name: score_sde_score_matching
description: Build continuous denoising score-matching targets, losses, and reduced optimizer evidence for Score SDE.
---

# Score SDE Score Matching

Use this skill when a recovery or implementation task needs the continuous denoising score-matching objective from the Score SDE paper. It is designed to consume marginal kernel outputs from a Score SDE implementation and can also run a deterministic reduced optimizer step for mechanism evidence.

Do not use this skill as a full neural-network trainer. It does not implement NCSN++, DDPM++, JAX, Flax, or dataset input pipelines.

## Inputs

- Clean data batch `x0`.
- Marginal means and standard deviations from a forward SDE kernel.
- Gaussian noise values and sampled times.
- A score model callable or the bundled linear score fixture.
- Loss mode: unweighted or likelihood weighted by `g(t)^2`.

## Outputs

- Perturbed examples.
- Conditional score targets for Gaussian perturbations.
- Per-example loss values and scalar average loss.
- Reduced optimizer trace with parameters before and after an update.

## Workflow

1. Build a batch using `build_score_matching_batch`.
2. Evaluate score predictions with an injected model.
3. Compute the continuous denoising score-matching loss.
4. For reduced recovery, call `optimizer_step` on a `LinearScoreModel`.
5. Save `loss_before`, `loss_after`, `params_before`, and `params_after` when using the optimizer trace as experiment evidence.

## Validation

Run:

```bash
python scripts/score_matching.py --self-test
python tests/test_score_matching.py
```

The tests check target construction, likelihood weighting, and a real parameter update.

## Limitations

The reduced optimizer uses finite differences for portability. Full paper reproduction requires a large neural score model and many training steps, which are outside this skill's bounded test contract.
