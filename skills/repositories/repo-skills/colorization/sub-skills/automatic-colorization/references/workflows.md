# Automatic colorization workflows

This sub-skill covers release-style automatic image colorization: load an RGB or grayscale image, extract the L channel at original and 256x256 resolution, run the selected colorizer to predict `ab`, resize/merge the result back to the original resolution, and save PNG files.

Use the bundled helper instead of reopening or running upstream release scripts:

```bash
python scripts/colorize_image.py --help
```

When invoking from outside this sub-skill directory, replace `scripts/colorize_image.py` with the relative path to this helper.

## Setup assumptions

1. Python can import the repo package `colorizers` either because the package is installed or because you pass `--repo-root` pointing at a local import root that contains `colorizers/`.
2. Install dependencies with corrected package names:

   ```bash
   python -m pip install torch numpy matplotlib pillow scikit-image ipython
   ```

   `argparse` is part of the Python standard library.
3. Quality runs use pretrained weights. On first use, `eccv16(pretrained=True)` and `siggraph17(pretrained=True)` ask PyTorch `torch.utils.model_zoo.load_url` to download public weights from `colorizers.s3...` URLs with hash checking. If the files are already cached by PyTorch, no network request is needed.
4. CUDA is optional. CPU works with a CPU-capable PyTorch install. CUDA runs require a CUDA-capable PyTorch build and a visible CUDA device.
5. The helper is headless by default. It sets a non-interactive Matplotlib backend and saves images only; `--no-display` is accepted for compatibility and does not change behavior.

Recommended variables used below:

```bash
REPO_ROOT="path/to/colorization"
INPUT_IMAGE="path/to/input.jpg"
OUT_DIR="outputs"
PREFIX="colorized"
```

## Colorize one image with both models on CPU

```bash
python scripts/colorize_image.py \
  --repo-root "$REPO_ROOT" \
  --input-image "$INPUT_IMAGE" \
  --output-dir "$OUT_DIR" \
  --save-prefix "$PREFIX" \
  --model both \
  --device cpu \
  --no-display
```

Expected files:

- `outputs/colorized_eccv16.png`
- `outputs/colorized_siggraph17.png`

The helper creates `--output-dir` if needed and overwrites existing files with the same names.

## Run exactly one model

ECCV16 only:

```bash
python scripts/colorize_image.py \
  --repo-root "$REPO_ROOT" \
  --input-image "$INPUT_IMAGE" \
  --output-dir "$OUT_DIR" \
  --save-prefix "$PREFIX" \
  --model eccv16 \
  --device cpu
```

Expected file:

- `outputs/colorized_eccv16.png`

SIGGRAPH17 automatic mode only:

```bash
python scripts/colorize_image.py \
  --repo-root "$REPO_ROOT" \
  --input-image "$INPUT_IMAGE" \
  --output-dir "$OUT_DIR" \
  --save-prefix "$PREFIX" \
  --model siggraph17 \
  --device cpu
```

Expected file:

- `outputs/colorized_siggraph17.png`

SIGGRAPH17 is used here in automatic mode with no user hints. For hint tensors or other programmatic variants, use the sibling Python API skill.

## CPU, CUDA, and auto device choices

- Force portable CPU execution:

  ```bash
  python scripts/colorize_image.py --repo-root "$REPO_ROOT" --input-image "$INPUT_IMAGE" --output-dir "$OUT_DIR" --save-prefix "$PREFIX" --model both --device cpu
  ```

- Force CUDA and fail fast if CUDA is unavailable:

  ```bash
  python scripts/colorize_image.py --repo-root "$REPO_ROOT" --input-image "$INPUT_IMAGE" --output-dir "$OUT_DIR" --save-prefix "$PREFIX" --model both --device cuda
  ```

- Use CUDA when PyTorch reports it is available, otherwise fall back to CPU:

  ```bash
  python scripts/colorize_image.py --repo-root "$REPO_ROOT" --input-image "$INPUT_IMAGE" --output-dir "$OUT_DIR" --save-prefix "$PREFIX" --model both --device auto
  ```

The helper moves both model and resized L tensor to the selected device, then moves predicted `ab` back to CPU before postprocessing and saving.

## Smoke checks without downloading weights

Use `--skip-pretrained` only to check imports, preprocessing, model construction, device placement, and file writing in an offline or no-download environment:

```bash
python scripts/colorize_image.py \
  --repo-root "$REPO_ROOT" \
  --input-image "$INPUT_IMAGE" \
  --output-dir "$OUT_DIR" \
  --save-prefix smoke \
  --model eccv16 \
  --device cpu \
  --skip-pretrained
```

The output from `--skip-pretrained` is not a meaningful colorization result because learned weights are not loaded.

## Validation checks

After a quality run:

1. Confirm the expected PNG files exist and are non-empty.
2. Confirm each output can be opened by Pillow.
3. Confirm each output has the same pixel dimensions as the input image; the model predicts at 256x256, then `postprocess_tens` upsamples the `ab` channels to the original L-channel size.
4. Visually inspect the result for plausible colorization. Do not require bit-for-bit equality across PyTorch, scikit-image, or Matplotlib versions.

Example structural check:

```bash
python - <<'PY'
from pathlib import Path
from PIL import Image

input_path = Path("path/to/input.jpg")
outputs = [
    Path("outputs/colorized_eccv16.png"),
    Path("outputs/colorized_siggraph17.png"),
]
input_size = Image.open(input_path).size
for output in outputs:
    assert output.is_file() and output.stat().st_size > 0, output
    with Image.open(output) as img:
        img.verify()
    with Image.open(output) as img:
        assert img.size == input_size, (output, img.size, input_size)
        print(output, img.size, img.mode)
PY
```

Adjust the paths and list of expected files to match `--model`, `--output-dir`, and `--save-prefix`.

## Mapping from the release workflow to this helper

| Release workflow behavior | Bundled helper behavior |
| --- | --- |
| Image flag `-i` / `--img_path` | `--input-image` |
| GPU flag `--use_gpu` | `--device cuda`; use `--device auto` to prefer CUDA but fall back to CPU |
| Save prefix flag `-o` / `--save_prefix` | Split into `--output-dir` plus `--save-prefix` |
| Loads both pretrained colorizers | `--model both` with pretrained loading enabled by default |
| ECCV16 and SIGGRAPH17 output suffixes | Saves `<prefix>_eccv16.png` and/or `<prefix>_siggraph17.png` in `--output-dir` |
| Preprocess, run model, postprocess sequence | Uses `load_img`, `preprocess_img(HW=(256,256))`, selected model forward pass, `postprocess_tens`, and `pyplot.imsave` |
| Interactive Matplotlib figure and display side effect | Removed; helper uses a headless backend and never calls display/show |

The historical Caffe training and representation-learning branch is outside this checkout-oriented automatic colorization workflow.
