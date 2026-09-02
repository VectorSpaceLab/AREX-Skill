---
name: sbi_neural_training
description: Train or proxy-train SBI density estimator families on simulator-generated parameter observation pairs.
---

# SBI Neural Training

Use this skill when simulation records need to be converted into a trained estimator for an `sbi`-style workflow. It covers the paper's SNPE, SNLE, and SNRE family distinction and provides a deterministic reduced SNPE-like proxy for environments where the full `sbi` and PyTorch stack is unavailable.

Do not report the reduced proxy as a full `sbi` run. The proxy is only valid when recovery mode permits reduced evidence and the runtime handoff records why the full stack is blocked.

## Inputs

- Valid simulation records with `theta` and `x` vectors.
- Algorithm family: `SNPE`, `SNLE`, or `SNRE`.
- Training parameters such as learning rate and optimizer steps.
- A reduced-runtime allowance flag when the full stack is unavailable.

## Outputs

- A trained estimator dictionary with scalar conditional-posterior parameters for reduced SNPE-style recovery.
- A training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and `optimizer_state_changed`.
- Family metadata identifying which paper algorithm family was represented.

## Workflow

1. Verify that records contain paired numeric `theta` and `x` values.
2. Select the SBI family. Full recovery should call the corresponding package trainer when available.
3. In reduced mode, train a scalar conditional Gaussian posterior mean `theta_hat = a * x + b`.
4. Record the parameter update and loss movement before and after optimization.
5. Pass the estimator to the posterior API skill for conditioning, sampling, and log-probability checks.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py /share/project/yuyang/workspace/Paperbench/record/case15/extracted_skills_attempt_001/sbi_toolkit/sbi_neural_training --run-tests
```

For a standalone smoke run:

```bash
python scripts/neural_training.py --demo
```

## Limitations

The reduced trainer is intentionally tiny and standard-library only. It preserves the simulator-to-estimator training mechanism but does not implement normalizing flows, MCMC, classifier ratio estimation, PyTorch autograd, or multi-round proposal adaptation.
