# JanusFlow Reference

## Purpose

Read this when a task mentions JanusFlow, rectified flow, SDXL VAE, or the JanusFlow-1.3B model family.

## Public imports

```python
from janus.janusflow.models import MultiModalityCausalLM, VLChatProcessor
```

For the text-to-image path, you also need diffusers:

```python
from diffusers.models import AutoencoderKL
```

## Verified JanusFlow specifics

The repository's JanusFlow code differs from Janus / Janus-Pro in several ways:

- The processor includes `image_gen_tag`.
- The understanding path counts `num_und_image_tokens` and includes the begin-of-image token in the image mask.
- The generation path uses a rectified-flow loop rather than the autoregressive image token loop used by Janus / Janus-Pro.
- The decoder path needs an SDXL VAE.
- The README explicitly notes that the VAE should use `bfloat16` instead of `fp16`.

## Generation pattern

A simplified version of the README / demo generation loop is:

1. Build a single-turn prompt and append `image_gen_tag`.
2. Encode the prompt with the tokenizer.
3. Duplicate the token batch for classifier-free guidance.
4. Remove the final generation token from the language embedding sequence.
5. Initialize `z` with shape `[batch_size, 4, 48, 48]`.
6. For each ODE step:
   - encode the latent with `vision_gen_enc_model`,
   - align the latent to the language model space,
   - append the timestep embedding and latent tokens to the LLM input,
   - decode the latent update with `vision_gen_dec_model`,
   - apply CFG and step the latent.
7. Decode the final latent with the SDXL VAE and save images.

## Important defaults from the repo

The published demo uses these baseline values:

- `cfg_weight=2.0`
- `num_inference_steps=30`
- `batch_size=5`
- latent shape `4 x 48 x 48`
- output resizing to a larger display image after decode

## Dependency compatibility note

The verified inspection environment found that `diffusers==0.36.0` failed with `torch==2.0.1` because the diffusers import path touched `torch.xpu`. `diffusers==0.30.3` imported successfully with that torch wheel.

If you see the same error, do not assume the JanusFlow code is broken; check the torch/diffusers compatibility first.
