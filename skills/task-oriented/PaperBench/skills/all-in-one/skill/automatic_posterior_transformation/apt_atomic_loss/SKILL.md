---
name: apt_atomic_loss
description: Evaluate equation-6 atomic APT categorical probabilities and density-ratio losses for finite parameter atom sets.
---

# APT Atomic Loss

Use this skill when APT cannot evaluate the transformed-density normalizer in closed form and a recovery can instead evaluate finite atom sets. The skill computes equation-6 probabilities and the cross-entropy loss for the generating parameter.

## Inputs

- A finite atom set `Theta`.
- Posterior-estimator log densities `log q(theta_i | x)`.
- Prior log densities `log p(theta_i)`.
- Index of the atom that generated the observation.

## Outputs

- Normalized atom probabilities.
- Atomic negative log likelihood.
- Ratio diagnostics showing whether probability ratios match posterior/prior score ratios.

## Workflow

1. Validate matching array lengths, a valid true index, and finite prior density for the true atom.
2. Compute scores `log_q_i - log_prior_i`.
3. Normalize scores with log-sum-exp.
4. Return `-log(probability[true_index])`.
5. Use ratio diagnostics for mechanism checks in reduced recovery.

## Validation

Run:

```bash
python tests/test_atomic_loss.py
```

The tests verify normalization, constant-shift invariance, score ordering, loss reduction after a targeted update, and rejection of a true atom outside prior support.

## Limitations

- This helper is deterministic and framework-free. It does not backpropagate through a neural network.
- Full APT with MAFs or MDNs should use the same probability semantics but would rely on a deep learning framework for gradients.
