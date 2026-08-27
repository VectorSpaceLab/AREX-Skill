---
name: face-alignment
description: "Routes face-alignment installation, import checks,
  landmark-detection workflows, and detector-backend selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Face-Alignment Repo Skill

Use this repo skill when a task names `face_alignment`, face landmark detection, 2D / 2.5D / 3D facial keypoints, or detector backends such as SFD, BlazeFace, YuNet, RetinaFace, SCRFD, folder boxes, or deprecated dlib.

## Start here

- Read `references/repo-provenance.md` when you need to know whether this skill still matches the current checkout.
- Run `scripts/check_install.py` after installing dependencies or when an import seems broken.
- Use `sub-skills/landmark-detection/` for image, batch, or directory landmark inference.
- Use `sub-skills/detectors/` when the question is which face detector backend to use or why one backend is unavailable.

## Install

The package distribution is `face-alignment` and the import name is `face_alignment`.

For a normal user install:

```bash
pip install face-alignment
```

For local source inspection from this checkout:

```bash
pip install -r requirements.txt
pip install -e .
```

If you need SCRFD support, install the optional extra:

```bash
pip install -e '.[scrfd]'
# or: pip install onnxruntime
```

If you plan to use RetinaFace, also install `torchvision` because that backend imports it directly.

The package requires Python 3.9+ and PyTorch 2.0+.

## Minimal check

```bash
python -c "import face_alignment; print(face_alignment.__version__)"
python scripts/check_install.py
```

## Route map

- `sub-skills/landmark-detection/` — run `FaceAlignment` on a single image, a batch tensor, or a directory of images; choose landmark type, device, compile, and batch-size settings; interpret returned landmark arrays and no-face results.
- `sub-skills/detectors/` — choose `face_detector=...`, handle optional detector dependencies, use `folder` sidecar boxes, and troubleshoot backend-specific import or device failures.

## Common choices

- Use `device='cpu'` on CPU-only systems; the class default is `device='cuda'`.
- Use `compile=False` when you want fast startup or a simpler smoke path.
- Use `flip_input=False` only when you want to skip the accuracy trade-off of test-time flipping.
- Read `references/api-reference.md` for the verified constructor, return shapes, and helper functions.
- Read `references/troubleshooting.md` for cross-cutting install, import, download, and device issues.
- Read `references/repo-routing-metadata.json` when you need to inspect the router-facing scenario placement or selection guidance.
