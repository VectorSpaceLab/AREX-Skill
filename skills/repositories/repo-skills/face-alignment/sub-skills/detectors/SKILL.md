---
name: detectors
description: "Routes face detector backend selection and backend-specific
  troubleshooting for face-alignment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Detector Backends

Use this sub-skill when the task is about choosing `face_detector=...`, understanding detector backend trade-offs, fixing missing optional dependencies, or using the `folder` detector with precomputed boxes.

## Common triggers

- `which detector should I use?`
- `sfd`, `blazeface`, `yunet`, `retinaface`, `scrfd`, `folder`, or `dlib`
- missing `onnxruntime`, `torchvision`, or `dlib`
- detector-specific kwargs like `back_model`, `filter_threshold`, `score_threshold`, or `confidence_threshold`
- precomputed boxes in `.npy`, `.t7`, or `.pth` files

## Read first

- `references/detector-overview.md` for supported backends, dependencies, device support, reference scales, and default kwargs.
- `references/troubleshooting.md` for missing optional packages, device warnings, and sidecar file errors.
- `../../references/api-reference.md` for the shared `FaceAlignment` and detector constructor signatures.
- `scripts/check_detector_support.py` when you want a safe backend-availability probe.
- `../landmark-detection/` if the user actually wants landmark predictions rather than backend selection.

## Route guidance

- `sfd` is the default PyTorch backend.
- `blazeface` is the speed-oriented PyTorch backend.
- `yunet` is the OpenCV DNN CPU-only backend.
- `retinaface` requires `torchvision`.
- `scrfd` requires `onnxruntime`.
- `folder` uses precomputed bounding boxes and is useful for evaluation or when detection is already done.
- `dlib` is deprecated; mention it only if the user already depends on it.
