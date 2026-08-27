# Data layouts

This repository uses `--dataset_mode` to choose how `--dataroot` is interpreted. Choose the mode from the task first, then validate the folders before constructing train/test commands.

## Supported image files

The bundled validators use the same extension coverage as the repository image loader:

```text
.jpg .JPG .jpeg .JPEG .png .PNG .ppm .PPM .bmp .BMP .tif .TIF .tiff .TIFF
```

Images are discovered recursively under the mode-specific folders. A directory that exists but contains zero supported image files will fail at runtime, even if it contains metadata files or unsupported image formats.

## Mode-to-layout map

| Dataset mode | Main workflow | `--dataroot` interpretation | Expected phases/folders | A/B meaning |
| --- | --- | --- | --- | --- |
| `unaligned` | CycleGAN (`--model cycle_gan`) | Root containing domain-specific folders. | Training uses `trainA/` and `trainB/`; testing commonly uses `testA/` and `testB/`. Other phases follow the same `<phase>A` and `<phase>B` pattern. | A and B are independent domain samples; filenames and counts may differ. Unless serial batching is selected, B samples are not paired with A samples. |
| `aligned` | pix2pix (`--model pix2pix`) and template-style paired data | Root containing phase folders of already combined side-by-side AB images. | Training uses `train/`; testing uses `test/`. Other phases use `val/`, custom `<phase>/`, etc. | Each image file is split vertically into left half A and right half B. `--direction AtoB` maps left to right; `--direction BtoA` maps right to left. |
| `single` | One-sided generator application (`--model test`) | `--dataroot` points directly at a folder of input images. | No automatic `train` or `test` suffix is appended. Point directly to the chosen image folder, such as a single-domain test folder. | Only A is loaded. Use this for applying one generator direction without loading a paired or two-domain dataset. |
| `colorization` | pix2pix-based colorization (`--model colorization`) | Root containing natural RGB image phase folders. | Training uses `train/`; testing uses `test/`. | No pre-combined AB files are needed. RGB images are converted internally into Lab space: A is L (`input_nc=1`), B is ab (`output_nc=2`), direction is `AtoB`. |

## Layout sketches

### Unaligned / CycleGAN

```text
DATASET_ROOT/
  trainA/  # domain A training images
  trainB/  # domain B training images
  testA/   # optional A-side holdout images
  testB/   # optional B-side holdout images
```

Use `--dataroot DATASET_ROOT --dataset_mode unaligned --model cycle_gan`. Domain folder counts can be different; the dataset length is the larger of A and B.

### Aligned / pix2pix

```text
DATASET_ROOT/
  train/   # side-by-side AB training images
  test/    # side-by-side AB test images
```

Each file is one RGB image with A on the left and B on the right. Pair raw A and B folders first with [`../scripts/combine_pairs.py`](../scripts/combine_pairs.py). If the task is label-to-photo but labels are stored on the right half, use `--direction BtoA`; if labels are on the left half, use `--direction AtoB`.

### Single-image inference

```text
SINGLE_INPUT_ROOT/
  image_001.jpg
  image_002.png
  nested/also_loaded.jpeg
```

Use `--model test`, which selects `single` loading, and point `--dataroot` directly at the images to translate. Do not point to the parent dataset root unless that parent itself contains the intended images.

### Colorization

```text
COLORIZATION_ROOT/
  train/   # natural RGB training images
  test/    # natural RGB test images
```

Do not run A/B pair combination for colorization. The loader derives L and ab channels from each RGB image and requires the colorization defaults `input_nc=1`, `output_nc=2`, and `direction=AtoB`.

## Validation recipes

Use these checks before moving to training or testing:

```bash
python sub-skills/data-preparation/scripts/validate_layout.py --mode unaligned --dataroot DATASET_ROOT
python sub-skills/data-preparation/scripts/validate_layout.py --mode aligned --dataroot DATASET_ROOT --check-open --check-aligned-width
python sub-skills/data-preparation/scripts/validate_layout.py --mode single --dataroot SINGLE_INPUT_ROOT
python sub-skills/data-preparation/scripts/validate_layout.py --mode colorization --dataroot COLORIZATION_ROOT --check-open
```

For a specific phase, add `--phase train`, `--phase test`, or `--phase val`. In auto mode the validator checks every standard phase folder it can find and reports missing optional test folders as warnings rather than hard failures.

## Creating aligned AB folders

If A and B data start as separate matched folders, prefer the bundled Pillow adapter:

```bash
python sub-skills/data-preparation/scripts/combine_pairs.py \
  --fold-a RAW/A/train --fold-b RAW/B/train --fold-ab DATASET_ROOT/train

python sub-skills/data-preparation/scripts/combine_pairs.py \
  --dataset-path DATASET_ROOT --splits train,test
```

The combiner requires matching filenames and equal image sizes. It never downloads data, never deletes inputs, and refuses to overwrite existing outputs unless `--overwrite` is passed.

## Cityscapes orientation after conversion

The bundled Cityscapes converter writes both pix2pix and CycleGAN-friendly outputs:

```text
CITYSCAPES_OUT/
  train/   # paired AB JPEGs, left=A photo, right=B color label map
  test/    # val split converted to test paired AB JPEGs
  trainA/  # photos
  trainB/  # color label maps
  testA/   # val photos
  testB/   # val color label maps
```

For labels-to-photos pix2pix, the converted paired images require `--direction BtoA` because labels are on the right half. For photos-to-labels, use `--direction AtoB`.
