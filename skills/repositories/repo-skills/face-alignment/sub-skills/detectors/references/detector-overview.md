# Detector Overview

## Purpose

Read this when you need to choose a face detector backend, understand backend-specific kwargs, or explain why a detector imports but still cannot run.

## Backend summary

| `face_detector=` | Core backend | Extra dependency | Device support | Reference scale | Key kwargs / notes |
| --- | --- | --- | --- | --- | --- |
| `sfd` | PyTorch SFD | none beyond base package | CPU / CUDA / MPS | 195 | Default backend; `filter_threshold` controls post-filtering |
| `blazeface` | PyTorch BlazeFace | none beyond base package | CPU / CUDA / MPS | 195 | `back_model`, `path_to_detector`, `path_to_anchor`, `min_score_thresh`, `min_suppression_threshold` |
| `yunet` | OpenCV FaceDetectorYN | `opencv-python>=4.5.4` | CPU only | 165 | Device argument is ignored if not CPU; `score_threshold`, `nms_threshold` |
| `retinaface` | PyTorch RetinaFace | `torchvision` | CPU / CUDA / MPS | 165 | `confidence_threshold`, `nms_threshold`, `path_to_detector` |
| `scrfd` | ONNX Runtime SCRFD | `onnxruntime` | CPU provider by default; CUDA provider if you intentionally install a GPU runtime | 165 | `confidence_threshold`, `nms_threshold`, `path_to_detector` |
| `folder` | Precomputed sidecar boxes | none | any | n/a | Loads `.npy`, `.t7`, or `.pth` sidecar files that match the image basename |
| `dlib` | Legacy dlib detector | `dlib` | CPU / CUDA | n/a | Deprecated; prefer a supported backend for new work |

## Practical chooser

- Choose `sfd` when you want the default documented backend and are happy to trade speed for accuracy.
- Choose `blazeface` when you want a faster PyTorch backend and can tune the `back_model` option.
- Choose `yunet` when you want a CPU-only OpenCV path with no torch detector weights.
- Choose `retinaface` when you already have `torchvision` in the environment and want another PyTorch backend.
- Choose `scrfd` when you want the ONNX Runtime path and are willing to install the optional `onnxruntime` extra.
- Choose `folder` when the detector step is already done or you are evaluating with known boxes.
- Choose `dlib` only for legacy compatibility.

## Shared backend notes

- `face_alignment.FaceAlignment` always routes through one detector backend unless you pick `folder`.
- The detector constructors live under `face_alignment.detection.<backend>.FaceDetector`.
- `face_detector_kwargs` is passed straight into the backend constructor.
- Some backends ignore the requested device or warn about unsupported accelerators; read the troubleshooting file before assuming the device setting failed.

## What the detector reference does not cover

- Landmark output shapes and batch / directory prediction are covered by `../landmark-detection/references/workflows.md`.
- Core API signatures are covered by `../../references/api-reference.md`.
