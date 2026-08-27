# Python API troubleshooting

## Purpose

Read this when a scripted DragGAN workflow fails because of tensor shape, point order, checkpoint, or backend mistakes.

## Common mistakes

### `drag_gan()` fails on CPU tensors

The current implementation hardcodes CUDA inside the drag loop.
Move the model, W latent, and all point tensors to CUDA before starting the optimization.

### Handle points appear to move the wrong way

The API uses `[y, x]` ordering for points.
If you pass `[x, y]` pairs, the drag motion will look wrong or appear to miss the target.

### The mask argument has no effect

That is expected in this snapshot.
The current drag loop accepts `mask` but does not enforce it.

### `class_idx` is ignored or errors

Conditional checkpoints need a valid class index.
Unconditional checkpoints ignore `class_idx`.

### Checkpoint loading is slow or fails

Confirm the checkpoint path matches the catalog and that the cache root is writable and reachable.
The helper may be downloading the file from the network the first time.

## When to stop

If the issue is actually a missing CUDA backend or a broken Gradio compatibility stack, fix the environment first and then return to the API workflow.
