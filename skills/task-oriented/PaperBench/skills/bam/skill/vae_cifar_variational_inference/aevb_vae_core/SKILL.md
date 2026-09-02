---
name: aevb_vae_core
description: Run a compact AEVB/VAE training step with encoder statistics, reparameterization, decoder reconstruction, analytic KL, and optimizer evidence.
---

# AEVB VAE Core

Use this skill when a recovery experiment must exercise the core Auto-Encoding Variational Bayes mechanism on image-like data. It is appropriate for reduced/proxy recovery when full dataset training is blocked, provided the proxy is declared.

## Inputs
- Proxy image batch JSON with values in `[0, 1]`.
- `latent_dim`, `learning_rate`, and `seed`.
- Optional output path for a training trace.

## Outputs
- Training trace JSON with reconstruction loss, KL, total loss before and after one optimizer step; positive `loss_delta` is desirable recovery evidence but callers should inspect the numeric trace because tiny stochastic steps can vary by seed and learning rate.
- `params_before` and `params_after` snapshots.
- Mechanism checks: encoder, reparameterization, decoder, reconstruction loss, KL, optimizer step.

## Workflow
1. Load image observations and flatten them.
2. Encode to `mu` and `logvar`.
3. Compute `z = mu + exp(0.5 * logvar) * epsilon`.
4. Decode `z` to Bernoulli reconstruction logits.
5. Compute BCE plus analytic Gaussian KL.
6. Update trainable parameters and record before/after signals.

## Validation
Run:

```bash
python scripts/run_vae_step.py --batch-json /tmp/vae_proxy_batch.json --output /tmp/vae_trace.json
python tests/test_vae_step.py
```

## Limitations
A tiny proxy trace is not a full paper reproduction. Keep `full_training_executed` false unless a real full dataset/model run was executed.
