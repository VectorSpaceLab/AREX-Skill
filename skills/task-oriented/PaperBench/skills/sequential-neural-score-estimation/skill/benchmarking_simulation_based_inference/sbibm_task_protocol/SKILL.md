---
name: sbibm_task_protocol
description: Build validated simulation-based inference benchmark task items with prior, simulator, observation, and reference posterior metadata.
---

# SBI Benchmark Task Protocol

Use this skill when a recovery experiment needs a small `sbibm`-style task without reading the original benchmark repository. It is appropriate for Gaussian Linear proxy recovery and for checking that downstream posterior and metric modules receive a complete task contract.

## Inputs
- Task name, currently `gaussian_linear_proxy` for deterministic recovery.
- Dimension, prior scale, simulator scale, observation seed, and optional explicit observation vector.
- Output path for the task item JSON.

## Outputs
- A JSON task item with prior parameters, simulator parameters, observation, analytic posterior mean/covariance, simulation budget, and provenance.
- Validation errors for invalid dimensions, scales, or observation lengths.

## Workflow
1. Choose a bounded Gaussian Linear proxy when full `sbibm` execution is unavailable.
2. Construct zero-mean Gaussian prior and Gaussian simulator noise.
3. Generate or validate one observation vector.
4. Compute the conjugate posterior parameters for one observation.
5. Record whether the item is benchmark-style or derived from concrete resources.

## Validation
Run `python tests/test_task_protocol.py` or validate the skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not reproduce all ten benchmark tasks. It preserves the paper mechanism for bounded recovery by exposing the same task-level contract used by SBI algorithms and metrics.
