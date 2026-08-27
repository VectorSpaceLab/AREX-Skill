# Testing workflows

## Runtime startup contract

`test.py` is a thin wrapper around `main(mode=2)`. In this mode the shared loader:

1. Parses `--path`/`--checkpoints` for the checkpoint directory and reads `config.yml` from that directory.
2. Creates the checkpoint directory if it does not exist.
3. If `config.yml` is absent, tries to copy a template named `config.yml.example` from the launch working directory. Prefer creating the intended `config.yml` yourself instead of relying on this fallback.
4. Forces `MODE = 2`.
5. Sets `MODEL` from `--model`; if `--model` is omitted, uses stage `3`.
6. Forces `INPUT_SIZE = 0`, so test images keep their original size after mask resizing.
7. Replaces `TEST_FLIST`, `TEST_MASK_FLIST`, `TEST_EDGE_FLIST`, and `RESULTS` when `--input`, `--mask`, `--edge`, and `--output` are supplied.
8. Sets visible CUDA devices from the config's `GPU` list, chooses CUDA when Torch reports it available, otherwise falls back to CPU.
9. Builds `EdgeConnect`, loads the selected stage weights, and runs the test loop.

Canonical command shape:

```bash
python test.py \
  --model <1|2|3|4> \
  --checkpoints <checkpoint-dir> \
  --input <image-file-or-dir-or-flist> \
  --mask <mask-file-or-dir-or-flist> \
  --output <output-dir>
```

`--path` is accepted as an alias for `--checkpoints`. Add `--edge <edge-file-or-dir-or-flist>` only when the checkpoint config uses external edges (`EDGE: 2`) or when you are intentionally overriding `TEST_EDGE_FLIST` for that config.

## Build a command without running it

Use the bundled command builder when you want a shell-safe command string to paste, review, or log:

```bash
python scripts/build_test_command.py \
  --model 3 \
  --checkpoints checkpoints/places2 \
  --input data/test/images \
  --mask data/test/masks \
  --output runs/edgeconnect-results
```

The helper prints only the command text and does not inspect checkpoints, import Torch, or run inference. Pair it with `scripts/check_checkpoints.py` before launch.

## Input forms and pairing

EdgeConnect test mode accepts image, mask, and optional edge paths in the same three forms:

| Form | Loader behavior | Pairing rule |
| --- | --- | --- |
| Single file | Treats the file as a one-item list | Use one image file with one mask file and, when needed, one edge file |
| Directory | Reads top-level `*.jpg` and `*.png`, sorted lexicographically | Image, mask, and edge directories must sort into the same order |
| Text flist | Reads paths from the text file | Each list must be index-aligned |

Important details:

- Directory loading is non-recursive and case-sensitive for the lower-case `*.jpg` and `*.png` patterns.
- Test mode forces one-to-one masks internally. The mask at index `i` is paired with the image at index `i`.
- Mask pixels greater than zero are treated as the missing region. White means "fill this area"; black means "keep this area".
- Masks are resized to the image size and thresholded, so the safest workflow is to prepare masks at the same size as their images.
- For output naming, the basename of each input image is reused. Duplicate basenames in a flist can overwrite earlier results in the same output directory.

## Single-file recipe

Use this for a quick manual inference case or a synthetic smoke case:

```bash
python test.py \
  --model 3 \
  --checkpoints checkpoints/places2 \
  --input data/single/case.png \
  --mask data/single/case-mask.png \
  --output runs/case-output
```

Expected behavior:

- One result image is written under `runs/case-output/` using the input image basename.
- The mask is resized to the image dimensions if needed.
- With the default Canny edge mode (`EDGE: 1`), no `--edge` argument is needed.

## Directory recipe

Use this when images and masks are already paired by sorted filenames:

```bash
python test.py \
  --model 3 \
  --checkpoints checkpoints/places2 \
  --input data/test/images \
  --mask data/test/masks \
  --output runs/test-output
```

Before running, confirm:

- Both directories contain only the intended top-level `.jpg` and `.png` files.
- The sorted image and mask lists have the same length.
- Basenames are unique enough that result files will not collide.
- If the config uses `EDGE: 2`, the edge directory or flist has the same ordering.

Flist creation and config path validation are owned by the `data-preparation` sub-skill.

## External-edge recipe

External edges are used only when `EDGE: 2` is set in `config.yml` inside the checkpoint directory.

```bash
python test.py \
  --model 2 \
  --checkpoints checkpoints/custom-inpaint \
  --input data/test/images \
  --mask data/test/masks \
  --edge data/test/edges \
  --output runs/inpaint-with-external-edges
```

Rules:

- Stage `1` uses the edge source as the known edge map outside the mask and predicts missing-region edges.
- Stage `2` uses the edge source directly as inpainting guidance.
- Stages `3` and `4` use the edge source as the known edge context outside the mask, then hallucinate missing-region edges before inpainting.
- If `NMS: 1`, external edges are multiplied by a Canny edge map after resizing.
- If `EDGE: 1`, a supplied `--edge` path is stored in the config object but the dataset still computes Canny edges; change the config to `EDGE: 2` if external edges are intended.

## Stage-specific inference behavior

| `--model` | Name | Required generator checkpoints | Test-time flow | Primary output |
| --- | --- | --- | --- | --- |
| `1` | Edge model | `EdgeModel_gen.pth` | Compute/load edges, predict missing-region edges, merge predicted edges inside the mask with known edges outside the mask | Edge image saved with the input basename |
| `2` | Inpaint model | `InpaintingModel_gen.pth` | Compute/load edges, inpaint RGB image from masked image plus edge guidance, merge generated RGB inside the mask with original RGB outside the mask | Inpainted RGB image saved with the input basename |
| `3` | Edge-inpaint model | `EdgeModel_gen.pth`, `InpaintingModel_gen.pth` | Predict edges with the edge model, then inpaint with the inpainting model | Inpainted RGB image saved with the input basename |
| `4` | Joint model | `EdgeModel_gen.pth`, `InpaintingModel_gen.pth` | Same inference path as stage `3`; the difference is how the checkpoints were trained | Inpainted RGB image saved with the input basename |

Discriminator files are not loaded in test mode, but they are part of the expected full checkpoint layout for resuming training.

## Output layout

The test loop creates the result directory before writing files.

- If `--output` is supplied, results go exactly there.
- If `--output` is omitted and the config has a `RESULTS` value, that value is used.
- If neither is supplied, results are written to `results/` under the checkpoint directory.

For each input image named `name.ext`, the main result is:

```text
<output-dir>/name.ext
```

The console prints the one-based index and basename as each image is saved.

## Debug outputs

When `DEBUG` in `config.yml` is nonzero, two extra images are saved beside each result:

```text
<output-dir>/name_edge.ext
<output-dir>/name_masked.ext
```

Meanings:

- `*_edge.ext` is the inverted edge tensor currently used by the loop. In stages `1` and `2`, this reflects the loaded or Canny-computed edge map. In stages `3` and `4`, it reflects the edge model output after the edge branch runs.
- `*_masked.ext` is the input image with the masked region shown as white.

Caution: debug naming splits the basename on a single dot. Filenames with multiple dots can fail during debug output creation; rename inputs or disable debug for those cases.

## Legacy runtime compatibility

This code path depends on legacy image and numeric APIs such as older SciPy image helpers and NumPy aliases, plus PyTorch behavior from the older project era. If a modern environment fails before model execution, use a legacy-compatible dependency set rather than treating the failure as an EdgeConnect model issue. CUDA is useful for practical inference speed, but the loader can map checkpoints to CPU when CUDA is unavailable.
