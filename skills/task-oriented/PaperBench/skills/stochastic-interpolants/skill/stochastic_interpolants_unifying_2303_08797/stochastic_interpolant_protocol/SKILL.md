---
name: stochastic_interpolant_protocol
description: Construct endpoint-valid stochastic interpolant samples with latent schedules and derivative targets for reduced or full generative recovery experiments.
---

# Stochastic Interpolant Protocol

Use this skill when a recovery or implementation needs to construct paper-faithful stochastic-interpolant tuples from endpoint samples. Do not use it as a sampler by itself; it only defines the bridge data used to learn fields.

## Inputs

- Endpoint values `x0` and `x1` with the same length.
- Time values `t` in `[0, 1]`, either one scalar or one value per sample.
- Latent noise `z` with the same length as the endpoints.
- Schedule name; the included script supports `linear_quadratic_gamma`.

## Outputs

- `x_t = (1 - t) x0 + t x1 + gamma(t) z`.
- `dot_x_t = x1 - x0 + gamma_dot(t) z`.
- `gamma`, `gamma_dot`, and endpoint-validity diagnostics.

## Workflow

1. Validate matching endpoint and latent vector lengths.
2. Broadcast scalar time or validate per-sample time values.
3. Use the linear interpolant and `gamma(t)=2t(1-t)` unless the caller supplies another validated implementation.
4. Keep score-related division outside this skill because `gamma=0` at endpoints.
5. Save diagnostics when the output is used as recovery evidence.

## Validation

Run:

```bash
python scripts/interpolant_protocol.py --demo
python tests/test_interpolant_protocol.py
```

## Limitations

This skill intentionally avoids neural models, endpoint coupling optimization, and source-repository assumptions. It preserves the paper's construction contract and leaves field learning to objective skills.
