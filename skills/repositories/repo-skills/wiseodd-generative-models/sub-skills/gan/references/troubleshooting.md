# GAN troubleshooting

## Shared execution shape

- In a source checkout, these scripts expect the working directory to be `GAN/<family>/` so the relative paths match.
- Input data is expected at `../../MNIST_data`.
- Samples are written to `out/` under the family directory.
- There is no CLI or packaged entry point; these are bare training loops.

## Compatibility matrix

| Symptom | Affects | Why it happens | Minimal recovery |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorflow.examples'` | all TensorFlow GAN scripts, and many PyTorch GAN scripts that reuse the TensorFlow MNIST loader | TensorFlow 2.21.0 no longer ships `tensorflow.examples.tutorials.mnist.input_data` | use a TF1-style compatibility environment or replace the loader with a modern MNIST source |
| `IndexError: invalid index of a 0-dim tensor` from `loss.data[0]` | most PyTorch GAN scripts | torch 2.13.0 rejects scalar indexing through `.data[0]` | replace `.data[0]` with `.item()` or pin an older torch build |
| `AttributeError: module 'numpy' has no attribute 'int'` | `GAN/mode_regularized_gan/mode_reg_gan_pytorch.py` | NumPy 2.5.1 removed `np.int` | replace with builtin `int` or pin `numpy<1.24` |
| `FileNotFoundError` for `../../MNIST_data` | all families | the script was launched from the wrong working directory | rerun from the family directory or rewrite the relative path |
| no PNGs appear in `out/` | all families | the output directory is not writable or training never reaches the save block | check permissions and whether the sample interval is reached |

## Family-specific gotchas

- `cGAN`, `ACGAN`, and `InfoGAN` need the label/code tensors shaped exactly as the script expects.
- `DiscoGAN`, `DualGAN`, and `COGAN` are two-domain scripts; they are the wrong choice for plain single-domain digit synthesis.
- `WGAN-GP` is TensorFlow-only; do not search for a PyTorch version.
- `GAP` and `GibbsNet` are PyTorch-only; do not search for TensorFlow counterparts.
- The PyTorch GAN files still depend on the TensorFlow MNIST loader, so a modern PyTorch install by itself does not make them runnable.
- Exact failure order depends on the file: `gan_pytorch.py` and `mode_reg_gan_pytorch.py` usually hit the shared MNIST-loader import first, while many other PyTorch GAN files also fail later on `loss.data[0]`.

## Shared references

- `../../../references/compatibility.md`
- `../../../references/troubleshooting.md`
- `../../../references/model-catalog.md`
