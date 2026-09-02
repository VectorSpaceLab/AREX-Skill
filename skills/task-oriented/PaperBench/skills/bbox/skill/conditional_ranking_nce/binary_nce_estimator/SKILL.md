---
name: binary_nce_estimator
description: Compute binary conditional NCE objectives and diagnose self-normalization failures in finite protocols.
---

# Binary NCE Estimator

Use this skill when a recovery needs the binary data-vs-noise objective from conditional NCE or needs to diagnose whether the binary objective is valid for a conditional model. The key check is whether the conditional partition function can be treated as constant in `x` or modeled explicitly.

Do not use this skill to claim full conditional-model consistency when `Z(x)` varies and no per-input normalizer is present.

## Inputs

- A `ConditionalNCEProtocol`.
- A score function and scalar offset.
- `K`, inherited from the protocol.
- Optional parameters for the Section 4.3 paper counterexample.

## Outputs

- Binary objective value.
- Data-vs-noise posterior `g(x,y;theta,c)`.
- Self-normalization diagnostics.
- Analytic binary optimum ratio for the Section 4.3 counterexample.

## Workflow

1. Compute `bar_s=s-log p_N`.
2. Compute:

```text
g(x,y;theta,c) = exp(bar_s(x,y;theta)-c) /
                 (exp(bar_s(x,y;theta)-c) + K)
```

3. Accumulate data and noise log terms.
4. Check partition variation across inputs.
5. For the Section 4.3 counterexample, expose the paper's analytic binary limit `theta1/theta2=3/7`.

## Validation

Run the Distiller validator with tests. The tests assert that the Section 4.3 true ratio is `1/3`, the binary limit is `3/7`, and the normalizers differ across inputs.

## Limitations

The included optimizer and analytic diagnostic are for finite recovery and mechanism checks. They are not a replacement for full neural NCE training.
