# Preprocessing

These modules reshape or clamp optimizer inputs before the learned LSTM sees
them. They are especially relevant when `StandardDeepLSTM` is configured with a
`preprocess_name` and `preprocess_options` pair.

## `Clamp`

`Clamp(min_value=None, max_value=None)` preserves the input shape and applies
an elementwise lower and/or upper bound.

- If only `min_value` is set, the output is `max(input, min_value)`.
- If only `max_value` is set, the output is `min(input, max_value)`.
- If both are set, both bounds are applied in sequence.

Use it when you want a simple safety bound without changing the tensor layout.

## `LogAndSign`

`LogAndSign(k)` implements the paper-style gradient encoding.
It expects a floating-point tensor with a known rank and returns a tensor whose
last dimension is doubled.

For an input with shape `[d1, ..., dn]`, the output shape is:

```text
[d1, ..., d(n-1), 2 * dn]
```

The transform is:

- `log = log(abs(gradients) + eps)`
- `clamped_log = Clamp(min_value=-1.0)(log / k)`
- `sign = Clamp(min_value=-1.0, max_value=1.0)(gradients * exp(k))`
- concatenate `[clamped_log, sign]` along the last axis

`eps` comes from the gradient dtype, so the input must be a real floating type.

## Practical notes

- `LogAndSign` requires `k`; the helper script defaults `k` to `5` when you
  pass `--preprocess LogAndSign` without inline options.
- `Clamp` and `LogAndSign` can both be used as standalone Sonnet modules or as
  the preprocessing stage inside `StandardDeepLSTM`.
- `LogAndSign` changes the feature width before the LSTM sees the input, so the
  network input size after preprocessing is larger than the original gradient
  width.
