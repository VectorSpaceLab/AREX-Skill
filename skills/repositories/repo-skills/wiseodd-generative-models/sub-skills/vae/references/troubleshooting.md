# VAE Troubleshooting

This page captures the VAE-family failure modes that matter on the current legacy-vs-modern stack.

## Observed current stack

- TensorFlow 2.21.0 is installed, but `tensorflow.examples.tutorials.mnist.input_data` is missing.
- NumPy 2.5.1 removes `np.int`; the repo also has other families that use `np.float`, so the root compatibility note owns the full alias-removal matrix.
- torch 2.13.0 rejects `loss.data[0]` on scalar tensors.

## Common failures and fixes

| Symptom | Affected scripts | Likely cause | Fast fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorflow.examples'` | All TensorFlow VAE scripts | modern TensorFlow removed the old MNIST helper | use a TensorFlow 1.x-compatible environment or patch to a modern MNIST loader |
| `IndexError: invalid index of a 0-dim tensor` or a failure at `loss.data[0]` | All PyTorch VAE scripts | modern torch no longer supports the legacy scalar access pattern | replace `loss.data[0]` with `loss.item()` or pin a legacy torch build |
| `AttributeError: module 'numpy' has no attribute 'int'` | `aae_pytorch.py`, `avb_pytorch.py` | NumPy 2.x removed the alias used in label conversion | replace `np.int` with builtin `int` |
| `FileNotFoundError` for `../../MNIST_data` | All scripts | script launched from the wrong working directory or MNIST data not seeded | `cd` into the family directory before launching, and keep the repo-level `MNIST_data` where the relative path expects it |
| No files appear under `out/` | All scripts | output is relative to the current working directory | confirm the run directory and look for zero-padded PNGs under the family-local `out/` folder |

## Practical recovery order

1. Decide which VAE family you actually need.
2. Decide whether you are staying on the legacy stack or patching to modern dependencies.
3. Fix the environment blocker first, then, in a source checkout, use the family directory as the launch point.
4. If you only need a routing answer, use `references/workflows.md` and the root catalog instead of opening the source tree.

## Cross-links

- Root compatibility: `../../../references/compatibility.md`
- Root troubleshooting: `../../../references/troubleshooting.md`
- Family workflows: `workflows.md`
