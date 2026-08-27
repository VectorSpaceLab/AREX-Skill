# Detector Backend Troubleshooting

## Purpose

Use this file when a specific detector backend is unavailable, warns about the device, or fails because its optional dependency is missing.

## Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: torchvision` when choosing RetinaFace | RetinaFace imports `torchvision` directly | Install `torchvision` into the same environment and retry `face_detector='retinaface'` |
| `ModuleNotFoundError: onnxruntime` when choosing SCRFD | The optional SCRFD dependency is missing | Install `face-alignment[scrfd]` or `onnxruntime` |
| `ModuleNotFoundError: dlib` | The deprecated legacy backend is not installed | Prefer a supported backend; install `dlib` only if you must keep legacy behavior |
| A device warning says the backend will fall back to CPU | The backend does not support the requested accelerator | Use the supported device for that backend or switch to a different detector |
| YuNet ignores `device='cuda'` or `device='mps'` | YuNet is an OpenCV CPU backend | Set `device='cpu'` and treat it as a CPU-only backend |
| `FileNotFoundError` or `TypeError` from `folder` | The sidecar box file is missing, has the wrong suffix, or does not contain a list of boxes | Create a matching `.npy`, `.t7`, or `.pth` sidecar file that stores a list of bounding boxes |
| A detector returns an empty list on an image that should contain faces | Thresholds are too strict, the image is not a good match for that backend, or the weights are not ready | Lower the backend threshold, switch detectors, or confirm the model download completed |

## Backend-specific recovery notes

- **SFD / BlazeFace / RetinaFace**: these are PyTorch backends. If the import works but the constructor fails, check the model download, the requested device, and the detector kwargs.
- **SCRFD**: the backend imports ONNX Runtime inside the constructor. If the package is missing, install the optional extra before retrying.
- **folder**: the detector expects a string path to an image file and looks for a same-basename sidecar file. It does not accept an image array or tensor.
- **dlib**: this backend is deprecated. If a user asks for it, note the deprecation and prefer another backend when possible.

## Where to go next

- Run `scripts/check_detector_support.py` to see which backends import in the current environment.
- Read `../landmark-detection/references/troubleshooting.md` when the backend is available but landmark inference still fails.
