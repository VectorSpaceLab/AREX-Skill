---
name: sbi_neural_inference_family_selector
description: Select SNPE, SNLE, or SNRE for a simulation-based inference task from estimator and posterior-access requirements.
---

# SBI Neural Inference Family Selector

Use this skill when deciding which neural SBI family best matches a simulator-based inference problem.

Do not use it to run training; it only emits a family recommendation and constraints.

## Inputs
- Desired estimator target: posterior, likelihood, or ratio.
- Whether direct amortized posterior sampling is needed.
- Whether MCMC posterior sampling is acceptable.
- Whether density evaluation is required.

## Outputs
- Recommended family: `SNPE`, `SNLE`, or `SNRE`.
- Objective description.
- Posterior construction requirements and limitations.

## Workflow
1. Prefer `SNPE` when the task needs direct conditional posterior estimation and amortized posterior sampling.
2. Prefer `SNLE` when the task needs learned likelihoods and can use MCMC for posterior sampling.
3. Prefer `SNRE` when density-ratio classification is appropriate and MCMC is acceptable.
4. Reject incompatible requests instead of overstating a family capability.

## Validation
Run:

```bash
python scripts/select_family.py --target posterior --direct-sampling
python tests/test_select_family.py
```

## Limitations
- SNRE estimates ratios, not direct likelihood values.
- Posterior density evaluation depends on the chosen posterior implementation.
