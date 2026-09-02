---
name: sbi_simulator_prior_protocol
description: Validate simulator, prior, observation, and simulation-record contracts for simulation-based inference recovery workflows.
---

# SBI Simulator Prior Protocol

Use this skill when a recovery or implementation task needs to turn black-box simulator outputs into clean training records for simulation-based inference. It is appropriate for `sbi`-style workflows where parameters are sampled from a prior, passed to a simulator, and paired with observations for a neural density estimator or classifier.

Do not use this skill to train an estimator or to sample from a posterior. Its output is validated data and metadata for downstream SBI training.

## Inputs

- Prior samples or a prior-grid specification with explicit parameter dimension.
- A simulator callable, simulator formula, or precomputed simulator outputs.
- Optional observation `x_o` and expected observation dimension.
- Optional records with simulator status values.

## Outputs

- Validated records with `theta`, `x`, and `status`.
- Metadata with `theta_dim`, `x_dim`, `num_requested`, `num_valid`, `num_failed`, and shape warnings.
- A training dataset containing only valid numeric records.

## Workflow

1. Normalize scalar parameters and observations to one-element float vectors.
2. Execute or ingest simulator outputs and build one record per parameter value.
3. Reject missing, nonnumeric, nonfinite, or dimension-inconsistent observations.
4. Preserve invalid records in the audit log while excluding them from training data.
5. Pass the valid `(theta, x)` records to an SBI training skill.

## Validation

Run the deterministic tests:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py /share/project/yuyang/workspace/Paperbench/record/case15/extracted_skills_attempt_001/sbi_toolkit/sbi_simulator_prior_protocol --run-tests
```

The included script can also be run directly on a tiny built-in example:

```bash
python scripts/simulator_protocol.py --demo
```

## Limitations

This skill does not implement `sbi` internals, PyTorch tensor conversion, joblib scheduling, or neural-network standardization. It preserves the paper mechanism at the data-boundary level and leaves estimator training and posterior APIs to downstream skills.
