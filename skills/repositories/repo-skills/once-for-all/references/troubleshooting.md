# Troubleshooting

## Purpose

Read this when installation, import, download, dataset, or backend checks fail.
The goal is to recognize the failure mode quickly and switch to the right fix
without reopening the original repository.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `InvalidVersion` during editable install | The source `setup.py` stamps a timestamp into the version string, which recent packaging tools may reject in editable mode. | Use a normal install (`pip install .`) or the published `ofa` package instead of editable mode. |
| `ImportError` when importing `torch` or `torchvision` | Mismatched wheel tags, missing CUDA runtime, or an incompatible package mix. | Reinstall a torch/torchvision pair that matches your Python version and backend, then rerun the smoke script. |
| `ofa_specialized` fails while downloading | The specialized-model helper fetches public configs or weights. | Retry with network access, cache the files, or stick to the supernet smoke path. |
| `ImageFolder` or path errors during evaluation | The evaluation path expects an ImageNet-style folder layout. | Point `--data-root` at a directory containing the expected validation split structure. |
| Missing `pyyaml`, `thop`, or `matplotlib` | Search helpers use optional extras that are not part of the minimal import path. | Install the search extras from `references/dependencies.md`. |
| CUDA smoke is empty or unavailable | The local torch wheel does not match the GPU stack. | Use a CUDA-enabled wheel that matches the driver, or stay on CPU for model-loading smoke. |

## Practical recovery hints

- For offline work, use `ofa_net(..., pretrained=False)` and the bundled smoke scripts.
- For search workflows without public downloads, start with the dummy-efficiency smoke and only enable the real latency or FLOPs tables when the needed files are cached.
- If a specialized-model run is only needed to check API shape, a model-load smoke is enough; save the ImageNet-style validation run for a GPU-backed session.
