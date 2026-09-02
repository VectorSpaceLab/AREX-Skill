---
name: sbi_task_protocol
description: Build and validate simulation-based inference benchmark task records with priors, simulators, observations, and reference posteriors.
---

# SBI Task Protocol

Use this skill when a recovery or benchmark experiment needs a small, auditable SBI task interface rather than a repository-specific task object. It is appropriate for Gaussian-linear reduced recoveries and for checking that a task exposes the same information required by the paper: prior, simulator, observation, dimensions, simulation budget, and reference posterior samples.

Do not use this skill to claim full `sbibm` compatibility. It implements a compact protocol and a Gaussian-linear helper that preserves the benchmark mechanism without importing the original repository.

## Inputs

- Task metadata: name, parameter dimension, data dimension, and simulation budget.
- Prior metadata: diagonal Gaussian mean and variance.
- Simulator metadata: Gaussian-linear noise variance.
- Conditioning observation vector.
- Optional random seed and sample counts.

## Outputs

- A normalized JSON task record.
- Prior samples, simulator outputs, and reference posterior samples when requested.
- Analytic reference posterior parameters for Gaussian-linear one-observation conditioning.

## Workflow

1. Normalize the task with `scripts/sbi_task_protocol.py normalize-task`.
2. Generate simulations with `scripts/sbi_task_protocol.py simulate`.
3. Compute reference posterior parameters with `scripts/sbi_task_protocol.py posterior`.
4. Sample the reference posterior with `scripts/sbi_task_protocol.py sample-reference`.
5. Keep all outputs JSON serializable and include the random seed in experiment logs.

## Validation

Run:

```bash
python scripts/sbi_task_protocol.py self-test
python tests/test_sbi_task_protocol.py
```

The Distiller skill-tree validator also runs the tests:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

## Limitations

The deterministic helper supports diagonal Gaussian priors and Gaussian-linear simulators. Other benchmark tasks should be represented with the same task contract but need their own simulator and reference posterior implementation.
