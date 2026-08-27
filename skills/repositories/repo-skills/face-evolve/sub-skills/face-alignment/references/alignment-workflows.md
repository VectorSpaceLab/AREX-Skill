# face.evoLVe alignment workflows

This reference distills the face.evoLVe MTCNN alignment path for future agents that need to detect faces, localize five landmarks, crop aligned faces, or pre-resize raw images before alignment. Use the bundled scripts in this sub-skill; do not run the original repository scripts directly.

## Expected input and output layout

The batch workflow expects an identity-folder tree:

```text
<source-root>/
  identity_a/
    image_001.jpg
    image_002.png
  identity_b/
    frame_0001.jpeg
```

`align_faces.py` writes the same identity names under `<dest-root>/`, with one aligned `.jpg` file per successfully aligned input image. Images that cannot be decoded, fail detection, or produce no landmarks are skipped and reported. Hidden files such as `.DS_Store` are ignored rather than deleted.

For training-ready ImageFolder counts, low-shot pruning, or train/validation layout checks, switch to the sibling `data-preparation` sub-skill after alignment.

## Core API facts

| Surface | Fact to preserve |
| --- | --- |
| `detect_faces(image, min_face_size=20.0, thresholds=[0.6, 0.7, 0.8], nms_thresholds=[0.7, 0.7, 0.7])` | Expects a `PIL.Image`; returns bounding boxes shaped like `[n_faces, 5]` and landmarks shaped like `[n_faces, 10]` when faces survive all three MTCNN stages. Landmark columns are five x-coordinates followed by five y-coordinates. |
| `get_reference_facial_points(default_square=True)` | Produces the square five-point template for 112x112 face crops; installed inspection confirmed shape `(5, 2)`. |
| `warp_and_crop_face(src_img, facial_pts, reference_pts, crop_size=(w, h))` | Applies the affine/similarity transform and returns a cropped NumPy image with the requested output size. The batch helper passes `crop_size=(crop_size, crop_size)`. |
| Crop-size scaling | For square crops, face.evoLVe scales the 112x112 reference template by `scale = crop_size / 112.0` before calling `warp_and_crop_face`. Use the same `crop_size` later in PyTorch/PaddlePaddle training configs. |

## Workflow: batch-align an identity folder

1. Ensure a local face.evoLVe checkout is available because the MTCNN `.npy` weights are not copied into this skill.
2. Choose a new destination root that is not equal to, inside, or above the source root.
3. Run the bundled helper:

```bash
python scripts/align_faces.py \
  --repo-root <face-evolve-checkout> \
  --source-root <raw-identity-root> \
  --dest-root <aligned-identity-root> \
  --crop-size 112
```

4. Inspect the summary counts. A small number of skips is normal for corrupt files, non-face images, side profiles, or occlusions; many skips usually means detector parameters, image scale, or source layout need attention.
5. Use the aligned destination root as the image source for downstream ImageFolder training or feature extraction; route those downstream tasks to `data-preparation`, `pytorch-training`, or `feature-extraction-verification` as appropriate.

## Workflow: tune detector parameters

The MTCNN detector exposes stage thresholds and NMS thresholds. The bundled aligner passes them through:

```bash
python scripts/align_faces.py \
  --repo-root <face-evolve-checkout> \
  --source-root <raw-identity-root> \
  --dest-root <aligned-identity-root> \
  --crop-size 112 \
  --min-face-size 20 \
  --thresholds 0.6 0.7 0.8 \
  --nms-thresholds 0.7 0.7 0.7
```

Parameter guidance:

- Lower `min-face-size` if real faces are small in the input images; raise it to speed up detection on high-resolution portraits where tiny faces are irrelevant.
- Lower one or more `thresholds` to recover hard faces, but expect more false positives. Raise them when non-face regions are being aligned.
- Lower `nms-thresholds` to suppress duplicate boxes around the same face. Raise them cautiously when nearby faces are being over-pruned.
- The batch helper aligns the first returned face. For group photos or multi-face identity folders, manually isolate the intended subject or build a custom one-image inspection flow before batch processing.

## Workflow: use a non-112 square crop

1. Pick the square crop edge (`112`, `224`, etc.).
2. Run `align_faces.py --crop-size <edge>`.
3. Keep downstream `INPUT_SIZE` or PaddlePaddle image-size settings consistent with this value.

The helper follows the source formula `reference = get_reference_facial_points(default_square=True) * (crop_size / 112.0)`. If a future workflow needs a non-square crop, use the API contract directly with an explicit `output_size=(width, height)` reference template instead of the batch helper.

## Workflow: resize large raw images before alignment

When raw images are very large and CPU alignment is slow, first create a separate resized tree:

```bash
python scripts/resize_faces.py \
  --source-root <raw-identity-root> \
  --dest-root <resized-identity-root> \
  --min-side 512
```

Then pass `<resized-identity-root>` as `--source-root` to `align_faces.py`. The resize helper preserves identity-folder names, writes `.jpg` files, downsizes only images whose larger side exceeds `--min-side`, and pads resized large images to a square with black borders. It is a speed/scale preprocessing step, not a replacement for MTCNN alignment.

## Validation checklist

- Destination root exists, is separate from the source root, and contains the expected identity subfolders.
- Every saved aligned crop has size `crop-size x crop-size`; every resized large image has a square edge equal to `--min-side`.
- Output filenames are normalized to `.jpg`; update downstream file-list expectations accordingly.
- Source files, including `.DS_Store` or corrupt images, were not deleted by the bundled scripts.
- Skipped-image counts are explainable: corrupt/unsupported input, no face, no landmarks, or multi-face ambiguity.
- A spot-check of several aligned crops shows eyes and mouth corners in stable positions before feature extraction or training.
