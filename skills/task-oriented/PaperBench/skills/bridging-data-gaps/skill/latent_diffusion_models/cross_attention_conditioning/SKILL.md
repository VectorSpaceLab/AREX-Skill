---
name: cross_attention_conditioning
description: Validate and run deterministic LDM-style cross-attention conditioning between latent features and modality tokens.
---

# Cross-Attention Conditioning

Use this skill when an LDM experiment must prove that conditioning tokens influence latent denoising features through cross-attention. It is suitable for reduced recovery, shape checks, and prompt/conditioning module tests. Do not use it to choose sampler settings or evaluate image quality.

## Inputs

- Latent feature matrix used as query input.
- Conditioning token matrix used as key/value input.
- Projection matrices for query, key, and value.
- Optional mask for unavailable conditioning tokens.

## Outputs

- Conditioned feature matrix.
- Attention probabilities with rows summing to one.
- Shape validation errors for incompatible inputs.
- Diagnostics showing conditioning sensitivity.

## Workflow

1. Validate that feature and token inputs are rectangular numeric matrices.
2. Project latent features to queries and conditioning tokens to keys and values.
3. Compute scaled dot-product attention with stable softmax.
4. Return conditioned values and probability diagnostics.
5. Keep sampling choices and final image decisions outside this module's contract.

## Validation

Run `python scripts/cross_attention.py --output /tmp/attention.json`. The included tests check probability normalization, output shape, conditioning sensitivity, and shape errors.

## Limitations

This is a deterministic reference implementation for mechanism validation. Production LDMs use tensor libraries, batched multi-head attention, residual blocks, and learned encoders.
