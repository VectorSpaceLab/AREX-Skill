---
name: landmark-detection
description: "Routes face landmark prediction on single images, batches, and
  directories with FaceAlignment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Landmark Detection

Use this sub-skill when a user wants to detect facial landmarks from an image path, NumPy array, torch tensor, batch tensor, or directory of images. It covers 2D, 2.5D, and 3D landmark outputs, `get_landmarks` / `get_landmarks_from_image`, and the device / compile / batch-size knobs that affect inference.

## Common triggers

- `detect face landmarks`
- `run face_alignment on an image`
- `process a directory of faces`
- `compare 2D vs 3D landmarks`
- `return landmark scores`
- `return bounding boxes`
- `disable compile`
- `reduce batch size`

## Read first

- `references/workflows.md` for end-to-end image, batch, and directory recipes.
- `references/troubleshooting.md` when inference fails, no faces are detected, compile slows startup, or batch size causes memory pressure.
- `../../references/api-reference.md` for the exact constructor and method signatures.
- `scripts/detect_landmarks.py` for a reusable smoke / demo helper.

## Workflow

1. Pick `LandmarksType.TWO_D`, `LandmarksType.TWO_HALF_D`, or `LandmarksType.THREE_D`.
2. Choose `device='cpu'`, `device='cuda'`, or `device='mps'` explicitly.
3. Use `flip_input=True` for accuracy and `compile=False` when you want fast startup or a simpler smoke path.
4. Pass a small `max_batch_size` if the detector finds many faces or the host is memory constrained.
5. Prefer `get_landmarks_from_image` for one image and `get_landmarks_from_directory` for image trees; `get_landmarks` is only a deprecated alias.

## Output reminders

- Landmarks are returned as a list of faces.
- 2D and 2.5D results are shaped `(68, 2)`.
- 3D results are shaped `(68, 3)`.
- When no faces are found, the API returns `None` or `(None, None, None)` depending on `return_bboxes` and `return_landmark_score`.

## Handoff to detectors

If the user is choosing or troubleshooting a backend, route to `../detectors/` instead of changing landmark logic here.
