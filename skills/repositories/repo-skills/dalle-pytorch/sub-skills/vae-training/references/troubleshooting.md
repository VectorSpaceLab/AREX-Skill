# VAE troubleshooting

## `image size must be a power of 2`

`DiscreteVAE` asserts `log2(image_size).is_integer()`. Use sizes like `64`, `128`, `256`, or `512`.

## `input must have the correct image size`

The tensor passed to `DiscreteVAE.forward` must have shape `(batch, channels, image_size, image_size)`. Resize/crop data consistently with the VAE constructor.

## `folder does not contain any images`

The helper uses `torchvision.datasets.ImageFolder`, so a flat image folder can appear empty. Put images under at least one class/dummy subdirectory.

## OpenAI VAE torch assertion

If `OpenAIDiscreteVAE()` raises `torch version must be <= 1.10`, do not fight the current environment unless the user explicitly needs OpenAI's released VAE. Prefer:

- train/load a `DiscreteVAE` checkpoint;
- use `VQGanVAE` with explicit paths;
- create a separate legacy torch environment only for OpenAI VAE.

## W&B login or network side effects

The VAE training helper logs to W&B and saves artifacts. For unattended or offline contexts, use W&B offline/disabled mode chosen by the user, or provide an API training loop instead.

## CUDA-only helper behavior

The helper calls `.cuda()` when not using DeepSpeed. If CUDA is unavailable, run API-level CPU checks with `scripts/tiny_vae_api_smoke.py` and write a custom loop instead of launching the helper.

## DeepSpeed VAE checkpoint directory

When using DeepSpeed, a partitioned checkpoint directory can be written in addition to the ordinary checkpoint. A later DALL-E training stage expects a standard `*.pt` VAE file; merging DeepSpeed-partitioned VAE checkpoints into DALL-E training is not supported by the source helper.
