# Resampler

## Purpose

Use this reference when the identity embedding projection path is the part that is failing or being customized.

## Verified constructor snapshot

Installed-package signature inspection confirmed:

```text
Resampler.__init__(self, dim=1024, depth=8, dim_head=64, heads=16, num_queries=8, embedding_dim=768, output_dim=1024, ff_mult=4)
```

## Role in InfiniteYou

- The outer pipeline supplies a 512-d ArcFace embedding, reshaped to `[1, 1, 512]` before projection.
- InfiniteYou instantiates the projection module with `dim=1280`, `depth=4`, `dim_head=64`, `heads=20`, `num_queries=image_proj_num_tokens`, `embedding_dim=512`, `output_dim=4096`, and `ff_mult=4`.
- The Resampler output becomes `controlnet_prompt_embeds` for the Flux controlnet wrapper.

## Internal structure

- A learned `latents` parameter is initialized with shape `[1, num_queries, dim]`.
- `proj_in` maps the face embedding width into the Resampler width.
- Each layer is a `PerceiverAttention` block followed by a `FeedForward` block, both wrapped in residual connections.
- `proj_out` maps the latent width to `output_dim`, and `LayerNorm` finishes the sequence.
- The forward path repeats the learned latents across the batch, mixes them with the input embedding, and returns one projected token sequence per query.

## Checkpoint expectations

- `image_proj_model.bin` is loaded with `torch.load(..., weights_only=True)` and the code expects a top-level `image_proj` entry.
- The checkpoint must match the chosen `num_queries`, `dim`, `depth`, `heads`, and `embedding_dim`.
- If you change `image_proj_num_tokens`, you need a checkpoint that was trained or exported for the same query count.
- If you swap to a different face encoder, you must update `embedding_dim` and the checkpoint to match the new encoder output width.

## Common customization mistakes

- Loading a plain state dict that does not wrap the weights under `image_proj`.
- Reusing a checkpoint after changing `image_proj_num_tokens`.
- Changing the face encoder output dimension without changing `embedding_dim`.
- Debugging the projection path while the module is still on CPU. The source moves the module to CUDA bf16 for the projection step and then returns it to CPU.

## What to check when editing the projection path

1. Confirm the `image_proj` entry exists in the checkpoint and that the tensor shapes match the current constructor arguments.
2. Confirm the ArcFace embedding still produces a single 512-d vector before `Resampler` sees it.
3. Confirm the projected token width still matches the controlnet prompt embedding width expected by the Flux pipeline.
