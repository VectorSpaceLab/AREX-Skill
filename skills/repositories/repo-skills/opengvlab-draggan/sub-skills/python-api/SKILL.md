---
name: python-api
description: "Routes DragGAN scripting tasks such as loading checkpoints,
  generating latents and images, and running the drag optimization loop from
  Python."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# python-api

Use this sub-skill when the task is about `draggan.draggan` or `draggan.utils`: loading a model, generating a W latent, synthesizing an image, preparing points, or writing a script around the drag loop.

## Start here

1. Run the bundled preflight:
   `../../scripts/check_install.py --mode api`
2. Read `references/api-reference.md` for the verified function signatures and return shapes.
3. Read `references/workflows.md` for a minimal scripted generation or drag loop.
4. Read `../../references/checkpoints.md` if you need checkpoint names or cache behavior.
5. Read `references/troubleshooting.md` if the tensor or device setup is failing.

## This sub-skill covers

- Loading a pretrained generator with `load_model()`.
- Creating W+ latents with `generate_W()`.
- Turning a latent back into an image with `generate_image()`.
- Running the iterative drag loop with `drag_gan()` and point tracking.
- Using the point and mask helpers in `draggan.utils`.

## This sub-skill does not cover

- Browser UI layout or Gradio launch flags.
- Docker packaging or checkpoint catalog browsing.
- Claims that the drag loop works on CPU or MPS as a verified path.

## Important cautions

- The verified drag loop is CUDA-only in this snapshot.
- Points are represented as `[y, x]` tensors on the same device as the model.
- The `mask` parameter is accepted by the current drag loop signature but is not enforced by the current implementation.
- Conditional checkpoints need an explicit `class_idx`; unconditional checkpoints ignore it.

## Helpful references

- `references/api-reference.md` for the verified signatures and shape notes.
- `references/workflows.md` for copyable Python recipes.
- `references/troubleshooting.md` for device, point-order, and mask mistakes.
- `../../references/checkpoints.md` for checkpoint names and the cache root.
