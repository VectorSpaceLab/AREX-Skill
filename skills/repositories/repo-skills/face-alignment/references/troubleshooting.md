# Troubleshooting

## Purpose

Use this file for cross-cutting install, import, download, device, and compile failures that affect the whole package.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError` during `import face_alignment` | The package or one of its runtime dependencies was not installed into the active environment | Run `python -m pip check`, then reinstall the package and its runtime dependencies in the intended environment |
| Missing `skimage`, `numba`, `opencv-python`, `scipy`, or `torch` | The base install was incomplete or the wrong environment is active | Re-run the package install in the same prefix and confirm `python` comes from that prefix |
| `ModuleNotFoundError: torchvision` when selecting RetinaFace | RetinaFace imports `torchvision` directly, but the base package does not declare it | Install `torchvision` into the same environment before using `face_detector='retinaface'` |
| `ModuleNotFoundError: onnxruntime` when selecting SCRFD | The optional SCRFD dependency is missing | Install `face-alignment[scrfd]` or `onnxruntime` |
| `ModuleNotFoundError: dlib` | The deprecated dlib backend is not installed | Prefer a supported backend; install `dlib` only if legacy code depends on it |
| `torch.compile failed (...)` warning | The compile path was not available or was too costly for the current environment | Re-run with `compile=False` and keep using eager mode |
| `No faces were detected.` | The chosen image, detector, thresholds, or bounding boxes did not produce a detection | Read the landmark-detection troubleshooting file, lower detector thresholds, or try a different backend |
| First run is slow and downloads models | Weights are fetched on demand into the torch cache | Wait for the download once, or pass pre-downloaded local paths when the backend supports them |
| Default `device='cuda'` fails on a CPU-only machine | The class default assumes CUDA | Pass `device='cpu'` explicitly |

## Cache and download notes

- Model weights are downloaded on first use through the torch hub cache.
- The cache location is under the user's torch hub directory, not the generated skill tree.
- If the host is behind a proxy or blocked from the model URLs, a backend may import but still fail when the constructor tries to fetch weights.

## Where to go next

- For image, batch, and directory inference problems, read `sub-skills/landmark-detection/references/troubleshooting.md`.
- For detector-specific backend or optional dependency problems, read `sub-skills/detectors/references/troubleshooting.md`.
