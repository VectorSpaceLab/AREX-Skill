---
name: sbi_posterior_api
description: Provide observation-conditioned posterior sampling and log-probability APIs for SBI recovery estimators.
---

# SBI Posterior API

Use this skill after an SBI estimator has been trained and a task needs to expose distribution-like posterior behavior. It represents the paper's `NeuralPosterior` abstraction: a common object conditioned on observations that can produce parameter samples and, when supported, density values.

Do not use this skill to run simulators or train estimator parameters. It consumes an estimator and validates posterior behavior.

## Inputs

- A trained full or reduced estimator.
- Observation `x_o` for conditioning.
- Number of posterior samples and optional random seed.
- Optional candidate `theta` values for log-probability evaluation.

## Outputs

- Posterior summary statistics such as mean and standard deviation.
- Posterior samples conditioned on the observation.
- Optional log-probability values for supported estimators.

## Workflow

1. Load or receive an estimator with a documented posterior parameterization.
2. Condition it on an observation.
3. Produce deterministic samples when a seed is supplied.
4. Evaluate log probability only when the estimator supports it.
5. Save posterior summaries for diagnostics and recovery analysis.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py /share/project/yuyang/workspace/Paperbench/record/case15/extracted_skills_attempt_001/sbi_toolkit/sbi_posterior_api --run-tests
```

For a standalone smoke run:

```bash
python scripts/posterior_api.py --demo
```

## Limitations

The bundled script implements a scalar Gaussian reduced posterior. Full `sbi` posteriors can use richer samplers and conditional density estimators, but recovery code should keep the same contract: condition, sample, summarize, and evaluate density only when valid.
