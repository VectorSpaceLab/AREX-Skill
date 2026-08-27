# Helmholtz Machine Troubleshooting

## Shared references

- Root catalog: `../../../references/model-catalog.md`
- Root compatibility: `../../../references/compatibility.md`
- Root troubleshooting: `../../../references/troubleshooting.md`

## Common failure modes

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorflow.examples'` | The script expects the old TensorFlow MNIST helper, but modern TensorFlow 2.21.0 does not ship it. | Use the root compatibility guidance and provide a legacy MNIST loader or a local replacement. The wake-sleep loop itself is still NumPy-only after loading. |
| `AttributeError: module 'numpy' has no attribute 'float'` | NumPy 2.5.1 removed the legacy alias used by this script when binarizing MNIST and when preparing batches for plotting. | Replace `np.float` with builtin `float` or `np.float64`, or pin a legacy NumPy build if you need the original script unchanged. NumPy 2.x also removes similar aliases such as `np.int` elsewhere in this repo. |
| `FileNotFoundError` for `../../MNIST_data` | The script uses a plain relative path, so running from the wrong directory points MNIST somewhere else. | In a source checkout, use the example's own working directory so `../../MNIST_data` resolves to repo-root `MNIST_data`, or rewrite the path relative to `__file__`. |
| `out/H.png` or `out/V.png` appears in the wrong place, or not at all | `out/` is also relative to the current working directory. | Ensure the working directory is the one you expect, or update the script to resolve `out/` explicitly. |
| Plot save errors on a headless machine | Matplotlib backend or write-permission issue. Matplotlib is available in the current environment, so the usual problem is backend selection or filesystem access rather than a missing package. | Switch to a non-interactive backend such as `Agg` and verify that the destination directory is writable. |

## Family-specific reminders

- There is no CLI, so do not look for flags or subcommands.
- The script is a legacy research example, not a packaged module.
- If the user only needs the explanation, you can describe the wake-sleep loop without trying to run the script on the modern stack.
