# Generation troubleshooting

## `trained DALL-E must exist`

The helper asserts that `--dalle_path` exists. If the user has a DeepSpeed checkpoint directory, inspect whether it contains an auxiliary payload and whether weights were consolidated before ordinary generation.

## `you trained DALL-E using ... but are trying to generate with ...`

The checkpoint stores `vae_class_name`. Match generation flags to training:

- use `--taming` and VQGAN paths only for VQGAN-trained checkpoints;
- do not set `--taming` for `DiscreteVAE` or OpenAI VAE checkpoints;
- if `vae_params` is present, generation reconstructs a `DiscreteVAE`.

## CUDA unavailable

The helper does `DALLE(...).cuda()` and tokenizes prompt tensors to CUDA. If CUDA is unavailable, use API-level CPU smoke or write a custom generation script that avoids `.cuda()`.

## OpenAI VAE and torch version

Generation without `vae_params` and without `--taming` uses `OpenAIDiscreteVAE`; modern torch can trip the `torch <= 1.10` assertion. Use a compatible legacy environment or a checkpoint with explicit VAE params/VQGAN paths.

## Output path surprises

Prompt strings become directory names with spaces replaced by underscores and a length cap. Avoid path separators or sensitive prompt text in shared output directories.

## Too many images or batch too large

Memory scales with `num_images`, `batch_size`, model depth/dim, image token length, and whether CLIP ranking is used. Reduce `--batch_size` first, then `--num_images`, or use a smaller checkpoint.
