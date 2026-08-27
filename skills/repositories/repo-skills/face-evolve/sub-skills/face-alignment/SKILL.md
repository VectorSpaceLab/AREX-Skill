---
name: face-alignment
description: "Align face identity folders with MTCNN detection, landmark
  localization, affine crops, and resize-before-align helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# face-alignment

Use this sub-skill when the request is about face.evoLVe's MTCNN-based face detection, landmark localization, affine alignment, crop-size scaling, or resize-before-align preprocessing.

Do not use this sub-skill for low-shot balancing or ImageFolder validation; route those to `data-preparation`. Do not use it for checkpoint feature extraction or verification; route those to `feature-extraction-verification`. PaddlePaddle duplicate alignment parity belongs with `paddle-workflows`.

## Read or run

- Read `references/alignment-workflows.md` when you need the expected identity-folder input/output layout, detector parameters, crop-size scaling, or validation checklist.
- Read `references/troubleshooting.md` when imports fail, landmarks are missing, multiple faces appear, corrupt images are skipped, colors look wrong, crop sizes are surprising, non-JPEG inputs are converted, or SyntaxWarnings appear.
- Run `scripts/align_faces.py` to batch-align a `source_root/<identity>/<image>` tree into a separate aligned destination tree.
- Run `scripts/resize_faces.py` before alignment when raw face images are very large and MTCNN detection is too slow.

## Operating contract

- `scripts/align_faces.py` requires `--repo-root` pointing to a local face.evoLVe checkout that contains the MTCNN helper code and `applications/align/{pnet,rnet,onet}.npy` weights; the weights are not bundled here and no downloads are attempted.
- The bundled scripts are deterministic, traverse identity folders in sorted order, never delete source inputs, reject overlapping source/destination roots, ignore hidden `.DS_Store`-style files, and normalize aligned or resized outputs to `.jpg`.
