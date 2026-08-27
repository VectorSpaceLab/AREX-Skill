# Metric Usage Troubleshooting

## Purpose

Read this when pairwise comparison or LPIPS optimization does not behave as expected.

## Common issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Distances look backwards | The inputs were not normalized as LPIPS expects. | Use the bundled helper scripts or normalize tensors to `[-1, 1]` before calling LPIPS directly. |
| The first run pauses on a model download | The pretrained torchvision trunk weights are not cached yet. | Allow the one-time download, or pre-cache the weights before running offline. |
| `--spatial` does nothing useful | You asked for a map but did not save or inspect it. | Add `--spatial_map_out path.png` so the helper writes the map to disk. |
| The spatial map is all black or nearly flat | The map has a small dynamic range. | Inspect the numeric output or rescale the saved image; the helper saves a normalized heatmap. |
| Custom image files fail to load | The file is not a standard RGB image that Pillow can read directly. | Convert the input to PNG or JPG before running the helper. |
| LPIPS on a pair of images is slow on CPU | CPU inference is used and the model is nontrivial. | Keep the defaults for smoke tests, or enable CUDA if your environment has a CUDA-capable Torch build. |
| `lpips_loss.py` or the old GUI demo blocks in a headless environment | The stock demo expects an interactive plotting backend. | Use `scripts/optimize_lpips.py`, which saves images instead of opening a window. |

## Notes on the bundled helpers

- The comparison helper defaults to the bundled example assets in `../../assets/examples/`.
- The optimization helper saves `initial.png`, `final.png`, and optional intermediate frames.
- The helpers already perform the `[-1, 1]` conversion for file inputs.

## When to read other files

- Read `../../references/api-reference.md` if you need the verified LPIPS constructor or forward signature.
- Read `../../references/bapps-dataset.md` if the problem is actually about BAPPS layout rather than direct image comparison.
