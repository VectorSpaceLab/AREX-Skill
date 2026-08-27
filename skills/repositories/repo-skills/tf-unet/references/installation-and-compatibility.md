# Installation and compatibility

## Package snapshot

- Distribution: `tf-unet`
- Import module: `tf_unet`
- Source snapshot version: `0.1.2`
- Verified runtime: Python `3.7.16`
- Verified TensorFlow: `1.15.5`

## Verified dependency set

The inspection environment succeeded with the following core packages:

| Package | Verified version | Why it matters |
| --- | --- | --- |
| `tensorflow` | `1.15.5` | The package uses TF1 graph/session APIs such as `tf.Session`, `tf.placeholder`, and `tf.reset_default_graph`. |
| `protobuf` | `3.20.3` | TensorFlow 1.15.x import fails with newer protobuf descriptor generation in this legacy stack. |
| `numpy` | `1.18.5` | Matches the TF1.15 wheel constraints and keeps legacy `np.bool` usage importable. |
| `click` | `8.1.8` | CLI launcher support. |
| `Pillow` | `9.5.0` | TIFF loading and image writing. |
| `matplotlib` | `3.5.3` | Plot helpers and notebook visualization. |
| `scipy` | `1.7.3` | Gaussian filtering in the astronomy launcher workflow. |
| `h5py` | `2.10.0` | HDF5-based launcher workflows. |

## Recommended environment shape

- Use a CPU-only environment for normal inspection and workflow routing.
- Prefer Python `3.7` when you need to reproduce the verified legacy runtime surface.
- Keep the install focused on the runtime dependencies above; do not add a full docs or test stack unless the task explicitly asks for it.
- Add Jupyter only when you need notebook execution or cell-by-cell inspection.

## Typical preparation order

1. Create a private Python 3.7 environment.
2. Install `tensorflow==1.15.5`.
3. Pin `protobuf==3.20.3` if TensorFlow import fails with descriptor errors.
4. Install the workflow packages: `click`, `Pillow`, `matplotlib`, `scipy`, and `h5py`.
5. Install the package distribution that exposes the `tf_unet` module.
6. Run `scripts/check_tf_unet_env.py`.

## Notes for future agents

- The repository documents TensorFlow as `>=1.0.0`, but the verified inspection surface is TF1.x only.
- A successful import of `tf_unet` is not enough on its own; always confirm a tiny model build and prediction path.
- External dataset workflows may need additional data files or domain tools, but those are not required for the core package import.
- If you see a protobuf descriptor error, keep the `protobuf==3.20.3` pin rather than chasing the newest release.
