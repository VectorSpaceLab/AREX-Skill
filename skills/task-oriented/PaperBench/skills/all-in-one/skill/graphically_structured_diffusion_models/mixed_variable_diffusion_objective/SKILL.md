---
name: mixed_variable_diffusion_objective
description: Encode mixed continuous and categorical variables and compute GSDM-style conditional diffusion denoising losses.
---

# Mixed Variable Diffusion Objective

Use this skill when a GSDM recovery needs deterministic diffusion mechanics for mixed continuous and discrete variables: one-hot categorical encoding, arbitrary observation masks, forward noising, decoding, and masked `x0` denoising loss.

Do not use this skill as a full neural diffusion implementation. It supplies the objective contract and small numerical helpers used by recovery and tests.

## Inputs

- Variable specs with `name`, `kind`, and optional `num_categories`.
- Values for each variable.
- Beta schedule and timestep.
- Noise vector.
- Prediction vector and optional loss mask.

## Outputs

- Encoded `x0` vector.
- Noisy `xt` vector.
- Observation mask expanded to encoded dimensions.
- Masked mean-squared denoising loss.
- Decoded categorical values by argmax.

## Workflow

1. Encode continuous values as scalar channels.
2. Encode categorical values as one-hot channel blocks.
3. Expand observed variable names to encoded dimensions.
4. Compute `alpha_bar_t` from the beta schedule.
5. Produce `xt = sqrt(alpha_bar_t) * x0 + sqrt(1 - alpha_bar_t) * noise`.
6. Compute masked MSE over latent dimensions.

## CLI

```bash
python scripts/diffusion_objective.py --demo --output /tmp/gsdm_objective.json
```

## Validation

```bash
python -m pytest tests
```

The tests cover categorical round-trips, the noising equation, and masked loss behavior.

## Limitations

The helpers use Python lists and floats for portability. They are intended for small recovery checks, not high-throughput training.
