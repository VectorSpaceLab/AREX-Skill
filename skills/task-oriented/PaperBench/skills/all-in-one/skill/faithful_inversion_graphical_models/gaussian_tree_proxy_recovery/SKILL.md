---
name: gaussian_tree_proxy_recovery
description: Execute a bounded reduced recovery for binary-tree Gaussian BNs using NaMI inverse contracts and a real standard-library optimizer step.
---

# Gaussian Tree Proxy Recovery

Use this skill when full neural amortized-inference recovery is blocked but soft-mode reduced recovery is allowed. It implements a small executable proxy for the paper's binary-tree Gaussian BN experiment.

## Inputs

- Binary-tree depth and seed.
- Ordered inverse factor contracts produced from NaMI inverse parents.
- Runtime handoff showing whether full package/model training is available.
- Recovery output directory.

## Outputs

- Complete synthetic Gaussian-tree samples with latent and observed values.
- A training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, gradients, and optimizer metadata.
- Mechanism checks distinguishing reduced proxy training from full neural training.

## Workflow

1. Generate a deterministic binary-tree Gaussian BN with observed leaves.
2. Draw complete samples from the generative model.
3. Use the supplied factor contracts to construct parent feature vectors for latent factors.
4. Initialize a tiny linear Gaussian student.
5. Compute supervised squared-error loss against the complete latent values.
6. Run one gradient-descent step and verify parameters changed and loss decreased.
7. Save the trace and report metrics.

## Validation

Run:

```bash
python tests/test_proxy.py
```

The tests use only the Python standard library.

## Limitations

This is a declared reduced recovery. It must not be reported as the paper's full Figure 6 reproduction, and it must keep full-training flags false when the runtime lacks the required numerical or neural packages.
