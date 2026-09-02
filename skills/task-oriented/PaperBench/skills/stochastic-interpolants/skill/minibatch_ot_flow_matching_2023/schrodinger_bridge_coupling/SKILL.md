---
name: schrodinger_bridge_coupling
description: Build small entropy-regularized coupling checks and bridge variance schedules for SB conditional flow matching.
---

# Schrödinger Bridge Coupling

Use this skill when a recovery or implementation needs a compact SB-CFM mechanism check: entropy-regularized pair weights and bridge variance behavior. Do not treat the simple row-normalized Gibbs helper as a full Sinkhorn solver for production transport.

## Inputs
- Source and target minibatches.
- Positive entropy coefficient `epsilon`.
- Time `t` and bandwidth `sigma` for the bridge variance schedule.

## Outputs
- Stabilized Gibbs weights derived from squared costs.
- Row-normalized coupling proxy for small tests.
- Bridge standard deviation `sigma * sqrt(t * (1 - t))`.

## Workflow
1. Compute squared costs between source and target points.
2. Convert costs to stabilized `exp(-cost / epsilon)` weights.
3. Normalize rows for a lightweight concentration diagnostic.
4. Compute bridge variance and verify endpoint behavior.

## Validation
Run `python tests/test_sb_coupling.py` or the Distiller skill-tree validator with tests enabled.

## Limitations
This skill supports reduced recovery checks. A full SB-CFM implementation should use Sinkhorn/IPF normalization and stochastic bridge sampling.
