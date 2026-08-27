# Keras legacy stack

## Version and runtime assumptions

The inspected repository snapshot documents a legacy Keras route:

- Python 3.x, with the verified smoke using Python 3.6
- `tensorflow-gpu==1.4.1`
- `keras==2.2.2`
- `pydot`
- `matplotlib`
- `scikit-image`
- `scikit-learn`
- `tqdm`
- `SimpleITK` (compatible wheel version verified in the smoke environment)

## Why this matters

This stack is intentionally old. Future agents should treat it as a historical
compatibility surface, not as a modern TensorFlow 2 route.

## What the smoke environment proved

- The local `segmentation_models` package can be imported from the repository's
  source tree when it is on `PYTHONPATH`.
- `Unet`, `Nestnet`, `Xnet`, `FPN`, and `PSPNet` all build successfully with
  `encoder_weights=None` on tiny CPU-friendly inputs.
- The builders still enforce backbone-dependent shape constraints.

## Practical implications

- Use a separate legacy environment from the PyTorch nnU-Net route.
- Prefer `encoder_weights=None` when you only need to inspect model structure.
- Expect warnings from the TensorFlow 1.x stack when running on a newer host.
- Do not assume the package root exports `__version__` just because a bundled
  version file exists.

## When to consult this reference

- The user asks whether the repo can be used with modern TensorFlow 2.
- The user needs to recreate the legacy environment or understand the pinned
  dependencies.
- A builder import works, but model construction or plotting fails because the
  old stack is incomplete.
