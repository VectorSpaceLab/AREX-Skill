---
name: score_sde_probability_flow
description: Build deterministic probability-flow ODE diagnostics and one-dimensional likelihood corrections for Score SDE recovery.
---

# Score SDE Probability Flow

Use this skill when a recovery experiment must show the deterministic ODE counterpart of the reverse SDE or a likelihood-style divergence check.

## Inputs

- State value.
- Time value.
- Forward drift and diffusion or simple VP-like coefficients.
- Score and score derivative for exact low-dimensional tests.

## Outputs

- ODE drift.
- Zero diffusion flag.
- Divergence and log-density correction.
- Finite-step diagnostic.

## Workflow

1. Compute probability-flow drift with half the reverse-SDE score correction.
2. Set diffusion to zero.
3. Compute exact one-dimensional divergence when using a linear score.
4. Apply one Euler step and accumulate the negative divergence as a log-density correction.
5. Record that this is a proxy diagnostic unless full image scaling is provided.

## Validation

Run:

```bash
python tests/test_probability_flow.py
python scripts/probability_flow.py --x 1.0 --t 0.5 --score-coeff -1.0
```

## Limitations

This skill validates probability-flow mechanics; it does not report CIFAR-10 bits/dim without the full trained model and data pipeline.
