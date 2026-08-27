# Face Alignment for ALAE Inputs

## When to read

Read this when a user has raw face images and needs ALAE-compatible sample images for reconstruction, style mixing, CelebA, CelebA-HQ, or FFHQ-style workflows.

## Source behavior distilled

The repository's original `align_faces.py` aligns every detected face in a hard-coded input directory named `celebs`, uses a hard-coded dlib predictor file named `shape_predictor_68_face_landmarks.dat`, and writes numbered PNGs under one of the sample directories:

- 1024 mode (`use_1024 = True`): `dataset_samples/faces/realign1024x1024`, `output_size=1024`, source call used a large transform size.
- 128 mode (`use_1024 = False`): `dataset_samples/faces/realign128x128`, `output_size=128`, `transform_size=512`.

The bundled helper `scripts/align_faces_alae.py` preserves the useful alignment logic but removes those hard-coded paths. It lazy-imports dlib so `--help` and `--dry-run` work without the optional face-alignment stack installed.

## Requirements

- Python with `numpy`, `Pillow`, and `scipy` for image transformation and padding.
- `dlib` for face detection and landmark prediction.
- A local `shape_predictor_68_face_landmarks.dat` file, usually downloaded separately from the dlib model distribution. The helper requires `--predictor` for real runs.
- Input images with detectable frontal faces. RGBA inputs are converted to RGB.

No network call is made by the bundled helper. It never assumes the source checkout path.

## Safe workflow

Shown relative to this sub-skill directory:

```bash
python scripts/align_faces_alae.py --help

python scripts/align_faces_alae.py \
  --input-dir <raw-face-image-dir> \
  --output-dir <ALAE repository root>/dataset_samples/faces/realign1024x1024 \
  --predictor <path-to>/shape_predictor_68_face_landmarks.dat \
  --output-size 1024 \
  --max-images 20 \
  --dry-run

python scripts/align_faces_alae.py \
  --input-dir <raw-face-image-dir> \
  --output-dir <ALAE repository root>/dataset_samples/faces/realign1024x1024 \
  --predictor <path-to>/shape_predictor_68_face_landmarks.dat \
  --output-size 1024
```

For a CelebA 128x128 workflow, change the output size and destination:

```bash
python scripts/align_faces_alae.py \
  --input-dir <raw-face-image-dir> \
  --output-dir <ALAE repository root>/dataset_samples/faces/realign128x128 \
  --predictor <path-to>/shape_predictor_68_face_landmarks.dat \
  --output-size 128 \
  --transform-size 512
```

Use `--max-images` for a small fixture run before aligning a large directory. Omit `--dry-run` only after the input directory, predictor, and output destination are correct.

## Output expectations

- Output files are sequential PNGs named `00000.png`, `00001.png`, and so on.
- If one source image contains multiple detected faces, each detected face becomes a separate output image.
- The output directory is created only during a real run. Dry-run mode prints what would be scanned and written.
- ALAE reconstruction and training sample previews expect regular image files under `DATASET.SAMPLES_PATH`; they do not require TFRecords.

## Choosing 1024 versus 128

- Use **1024** for FFHQ and CelebA-HQ style sample layouts. These presets point to `dataset_samples/faces/realign1024x1024`.
- Use **128** for the CelebA 128x128 preset. That config points to `dataset_samples/faces/realign128x128`.
- If the user creates a custom config, choose `output_size = 2 ** (MODEL.LAYER_COUNT + 1)` for image workflows and keep `DATASET.SAMPLES_PATH` aligned with that size.

## Validation after alignment

After producing images, run the layout validator against the config that will consume them:

```bash
python scripts/validate_alae_data_layout.py \
  --config-file <ALAE repository root>/configs/ffhq.yaml \
  --repo-root <ALAE repository root> \
  --strict
```

For style mixing, also ensure `DATASET.STYLE_MIX_PATH` has separate `src/` and `dst/` image folders; face-aligned outputs can be copied or selected into those folders when appropriate.
