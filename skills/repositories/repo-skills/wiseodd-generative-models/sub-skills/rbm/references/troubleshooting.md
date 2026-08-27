# RBM Troubleshooting

This page focuses on the binary RBM scripts in `RBM/` and the problems that show up on a modern stack.

## Common failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorflow.examples'` | The scripts import the TensorFlow 1.x MNIST helper, which is missing from modern TensorFlow builds. | Use a legacy TF1-compatible environment or replace the loader with a modern MNIST source before rerunning. See `../../../references/compatibility.md`. |
| `AttributeError: module 'numpy' has no attribute 'float'` | NumPy 2.x removed `np.float`; the RBM scripts still cast with that alias. | Pin `numpy<1.24` or change `astype(np.float)` to `astype(float)`. |
| `FileNotFoundError` for `MNIST_data` | The scripts resolve `../MNIST_data` relative to the current working directory. | Launch from `RBM/`, or update the path if you are intentionally running elsewhere. |
| Output PNGs appear in an unexpected place | `out/` is created relative to the working directory, not the repository root. | In a source checkout, `RBM/` is the working directory that yields the default `RBM/out/` location. |
| Plot reshape / grid errors | `h_dim` is no longer a perfect square, or the plotting helper no longer matches the latent shape. | Keep `h_dim` square, or update the plotting helper together with the latent dimension. |
| The script runs but appears to do nothing useful | There is no CLI, progress bar, or evaluation harness; the loop is a long legacy training script. | Check the saved images in `out/` and the embedded hyperparameters in source. |

## RBM-specific notes

- The data loader asks for `one_hot=True`, but the labels are not used by the RBM update.
- The visible units are thresholded to binary values before training and before the final visualizations.
- The code is NumPy + matplotlib training logic, but the MNIST import still comes from TensorFlow 1.x-era APIs.
- matplotlib only handles the saved preview grids; in the current modern probe it is already available, so missing-output problems are more likely path or working-directory issues than a missing plotting package.

## Where to look next

- Root compatibility summary: `../../../references/compatibility.md`
- Root troubleshooting: `../../../references/troubleshooting.md`
- Exact script inventory: `../../../references/model-catalog.md`
