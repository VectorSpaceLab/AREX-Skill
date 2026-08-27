# Flax / TPU notes

This path is optional and experimental compared with the main Torch workflow.
Use it only when you are specifically working on the JAX/Flax pipeline or a TPU
runtime.

## Public surface

- `FlaxStableDiffusionWalkPipeline`
- `generate_images_flax(...)`
- `FlaxStableDiffusionWalkPipeline.walk(...)`
- `FlaxStableDiffusionWalkPipeline.make_clip_frames(...)`
- `pad_along_axis(...)`

## What is different

- The pipeline uses JAX/Flax arrays and `pmap` helpers.
- `jit=True` assumes the parameters are already replicated.
- Batch sizing is tied to `jax.device_count()`.
- The code pads batches so they can be sharded cleanly across TPU cores.
- `RealESRGANModel` upsampling is still a Torch-side helper and is not the main
  focus of this path.

## Practical guidance

- Treat this as a separate backend story from the main CUDA Torch workflow.
- Only use it when the user names Flax, JAX, TPU, or the flax notebook.
- If you do not have a supported accelerator, keep this path reference-only.

## Troubleshooting hints

- Ensure `jax`, `flax`, and the Diffusers Flax components are installed
  together.
- Confirm that `jax.device_count()` matches the accelerator layout you expect.
- If the batch shape is wrong, check the padding logic before the `shard`
  operation.
- `negative_prompt` handling is more constrained here than in the Torch path.

## Reference material

The main notebook-style workflow in the source repo is the best evidence for the
original TPU usage pattern. Keep the runtime skill self-contained by relying on
this distilled summary instead of the original notebook.
