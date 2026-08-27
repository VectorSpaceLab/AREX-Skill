# Model Reference Troubleshooting

## Purpose

Use this when the model smoke or model instantiation fails for one architecture but not others.

## Common problems

### ConditionalVAE complains about labels

**Symptoms:** shape mismatch, concatenation errors, or a `TypeError` when the labels are passed positionally.

**Likely cause:** `ConditionalVAE` expects a label vector, not a scalar class id, and the public API uses the `labels=` keyword.

**Recovery:** pass a float tensor of shape `[batch, num_classes]` through `labels=...` and route the same label tensor to `sample()` when needed.

### `VQVAE.sample()` fails

**Symptoms:** a `Warning` or message that the sampler is not implemented.

**Likely cause:** the model intentionally leaves `sample()` unimplemented.

**Recovery:** use `forward()` / `generate()` for reconstruction checks instead of expecting free sampling. If `torchsummary` errors on this model, rely on the forward/generate smoke instead of the summary path.

### VampVAE sample or forward path needs CUDA inputs

**Symptoms:** `.cuda()` or device errors when calling `sample()` or when a test moves the model to CUDA but leaves the input on CPU.

**Likely cause:** the implementation uses CUDA-specific sampling code and expects model inputs to live on the same device.

**Recovery:** run the smoke on a CUDA host, move the input tensor to the same device as the model, and pass a CUDA device index when sampling.

### DFCVAE tries to fetch pretrained features

**Symptoms:** instantiation stalls or hits a network call during the feature-network setup.

**Likely cause:** the model creates `vgg19_bn(pretrained=True)`.

**Recovery:** allow the download, cache the weights, or skip DFCVAE in offline-only sessions.

### `FactorVAE.loss_function()` needs more than `M_N`

**Symptoms:** `TypeError` about missing keyword arguments or a mismatch between the loss inputs and the forward output.

**Likely cause:** the discriminator branch depends on `optimizer_idx` and `batch_idx`.

**Recovery:** follow the loss signature in `api-reference.md` and the training path's dual-optimizer notes.

### A model is missing from the registry

**Symptoms:** key lookup fails when the smoke script tries to instantiate a model name from the config.

**Likely cause:** the name does not match `models.vae_models` or the config is stale.

**Recovery:** compare the config name against the registry table in `api-reference.md` and the overview map.
