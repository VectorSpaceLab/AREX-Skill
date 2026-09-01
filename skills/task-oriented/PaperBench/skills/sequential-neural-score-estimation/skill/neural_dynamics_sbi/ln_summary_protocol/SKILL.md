---
name: ln_summary_protocol
description: Build likelihood-free linear-nonlinear neural simulations and STA/firing-rate summaries for SNPE-style posterior recovery.
---

# LN Summary Protocol

Use this skill when a recovery or experiment needs a small mechanistic neural simulator with summary features matching the paper's LN receptive-field example. Do not use it as a generic classifier or as a likelihood evaluator.

## Inputs
- `theta`: receptive-field/filter vector.
- `n_stimuli`, `dimension`, and `seed` for deterministic stimulus generation.
- Optional `bias` and `gain` for Bernoulli spike probabilities.

## Outputs
- A JSON-compatible item containing `theta`, `stimuli`, `spikes`, `summary`, `sta`, `firing_rate`, and metadata.

## Workflow
1. Generate white-noise stimuli from a seeded RNG.
2. Apply a logistic nonlinearity to stimulus-filter projections.
3. Sample Bernoulli spikes without evaluating a likelihood.
4. Compute STA from spike-triggering stimuli and append firing rate.
5. Save the generated data item when used in recovery.

## Validation
Run `python tests/test_ln_summary.py` from this skill directory.

## Limitations
This is a reduced LN simulator for fast mechanism checks. It is not the full paper implementation and does not reproduce high-dimensional CNN/MDN experiments.
