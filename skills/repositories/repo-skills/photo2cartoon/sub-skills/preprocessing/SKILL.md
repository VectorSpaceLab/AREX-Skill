---
name: preprocessing
description: "Operate Photo2Cartoon face alignment, crop, segmentation-mask,
  alpha, and whitening preprocessing contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# preprocessing

Use this sub-skill when a task needs the Photo2Cartoon preprocessing contract: face landmark detection, largest-face selection, eye-corner rotation alignment, expanded square face crop, TensorFlow segmentation-mask handling, RGBA composition, or white-background compositing before training or portrait inference.

## Route Map

- Use this sub-skill for `Preprocess.process`, `FaceDetect.align`, crop expansion ratios, detector selection (`dlib` or `sfd`), segmentation graph tensor names, and alpha-mask semantics.
- Route generator execution, PyTorch/ONNX model weights, Cog prediction, and cartoon output postprocessing to sibling sub-skill `portrait-inference`.
- Route dataset directory layout, batch data preparation policy, and training CLI/checkpoint behavior to sibling sub-skill `data-and-training`.

## First Steps

1. Confirm the input image is RGB `uint8` with shape `H x W x 3`; convert OpenCV `BGR` inputs to RGB before calling preprocessing.
2. Confirm external preprocessing assets are available when doing real segmentation: the portrait segmentation graph is named `seg_model_384.pb` and is expected beside the preprocessing utilities in a repo checkout. It is not bundled in this skill.
3. Choose face-alignment backend deliberately: `detector='dlib'` is the default; `detector='sfd'` may be useful when installed and supported by the local `face_alignment` package. Use `device='cuda'` only when the detector stack and PyTorch/TensorFlow stack are GPU-compatible.
4. For source-contract checks that do not import TensorFlow, dlib, or the repo package, run the bundled checker:

```bash
python scripts/preprocess_contract_check.py --help
python scripts/preprocess_contract_check.py --repo-root /path/to/photo2cartoon-checkout
```

5. For batch preprocessing, build a guarded command with the bundled helper and add `--execute` only after assets/dependencies are verified:

```bash
python scripts/build_preprocess_command.py \
  --repo-root /path/to/photo2cartoon-checkout \
  --data-path /path/to/raw-portrait-folder \
  --save-path /path/to/preprocessed-output-folder
```

## Runtime Contract

- `Preprocess.process(image)` returns `None` when no face landmarks are detected.
- On success it returns an `Hc x Wc x 4` `uint8`-style RGBA array: first three channels are the aligned/cropped RGB face, and channel 4 is the resized segmentation alpha mask.
- The crop stage fills out-of-frame regions with white (`255`) before inserting the visible source pixels, so border padding is expected for near-edge faces.
- Background whitening uses `mask = alpha[:, :, None] / 255.0` and `face * mask + (1 - mask) * 255`.

Read [references/preprocessing-pipeline.md](references/preprocessing-pipeline.md) for the exact algorithm and API patterns. Read [references/troubleshooting.md](references/troubleshooting.md) for missing assets, TensorFlow compatibility, detector installation, no/multiple-face handling, crop padding, and alpha-mask shape failures.
