# Troubleshooting

Classify the failure before changing a flag. Keep the config, model, dataset,
checkpoint, TTA, patch shape, and output format as one reproducible tuple.

## CUDA and dependency failures

**`Torch not compiled with CUDA enabled`, no device, or `.cuda()` failure**

- These entry points unconditionally move the model/input to CUDA; there is no
  supported CPU fallback.
- Verify the prepared environment with `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`.
- Use the documented CUDA-compatible torch stack (the verified inspection used
  torch 2.0.1+cu118 on an A100) and run `python -m pip check`.
- Do not claim a real inference pass after only a CPU import or `--help` check.

**`ModuleNotFoundError` for `ttach`, `albumentations`, `catalyst`, or
`skimage`**

Install the repository's tested dependency set in the isolated environment.
`ttach` is required by all inference scripts; `catalyst` and `skimage` are
imported by the two inference scripts even though the main prediction path is
not a Catalyst runner. The source uses `pytorch-lightning`; the inspected
runtime used 2.3.0. Avoid mixing the incompatible `lightning` meta-package into
this environment without rechecking imports.

**PyramidMamba import failure**

`geoseg.models.PyramidMamba` imports optional `mamba_ssm`/`causal-conv1d` and
was not verified. Select a verified config/model (for example UNetFormer,
FT-UNetFormer, or DCSwin) or install and separately validate the optional CUDA
extension. Do not silently substitute a different architecture for a trained
checkpoint.

## Config and checkpoint failures

**Checkpoint not found**

The scripts construct `<weights_path>/<test_weights_name>.ckpt`, with relative
paths resolved from the current working directory. Run from the repository
root, inspect those two config values, and check the exact filename. The
checkout intentionally contains no `model_weights/` or `pretrain_weights/`.
For LoveDA DCSwin, also provide the configured external backbone
`pretrain_weights/stseg_small.pth` if the config builds it.

**`Unexpected key(s)`, missing keys, size mismatch, or class-head mismatch**

The checkpoint must come from the same dataset class count and compatible model
configuration. Confirm model family, decoder settings, auxiliary-loss shape,
number of classes, and checkpoint naming before retrying. A load that can be
forced by dropping keys is not equivalent to a verified result; the standard
scripts use Lightning checkpoint loading, not a general cross-model adapter.

**Config import raises `FileNotFoundError` under LoveDA**

`loveda_dataset.py` instantiates a validation dataset at module import. Create
the complete `data/LoveDA/Val/Urban/{images_png,masks_png_convert}` and
`Val/Rural/...` trees (and the test image tree for test prediction), or use a
config whose dataset module does not have this import-time data dependency.
This is a known source limitation, not a checkpoint error.

**UAVid fails at `config.gpus[0]` or selects the wrong device**

`inference_uavid.py` indexes `config.gpus[0]`; training configs commonly use
`gpus='auto'`. Use an indexable, explicit device selection in the inference
config (for example `[0]` for the first GPU), then verify the resulting model
and tensors are on the intended device. Keep the change in the run record.

## Data and CLI failures

**Tile dataset reports missing folder, empty dataset, or assertion on counts**

Check the exact dataset root and child names. Vaihingen/Potsdam test defaults
are `images_1024` and `masks_1024`; LoveDA needs region folders `Urban` and
`Rural` plus `images_png` (and masks for validation). The dataset enumerates
files with `os.listdir` and asserts equal image/mask counts for paired tile
datasets. Equal counts are insufficient: image/mask stems and extensions must
also pair.

**UAVid produces no labels**

The source searches `<sequence>/Images` only and accepts `.tif`, `.png`, and
`.jpg`. It does not recursively search, read a different folder name, or
require input `Labels`. Ensure the sequence root is passed to `-i`, not a
single `Images` folder, and inspect the output for empty sequence directories.

**Huge-image route produces no outputs**

Its input must be an existing flat folder with first-level `.tif`, `.png`, or
`.jpg` files. It does not recurse into UAVid sequences. Ensure the output root
is writable and distinct from the input folder so an output cannot be mistaken
for a source image on a rerun.

**`invalid choice` for TTA**

Use `-t lr` or `-t d4`, or omit the option for no TTA. The parser's Python
`None` choice does not mean that the shell string `None` is accepted.

**Unknown `-d` dataset**

UAVid accepts `pv`, `landcoverai`, and `uavid`. Huge-image inference additionally
accepts `building`. `-d` changes only the output color mapping; it does not
change the model's class count. Select the mapping that matches the model and
verify [output formats](output-formats.md).

## Output and palette failures

**Output directory is missing or filenames are absent**

Tile scripts create the requested root; LoveDA `--val` creates its `Urban` and
`Rural` subdirectories. In LoveDA test mode, the source writes directly under
the output root and can collide if Urban and Rural contain the same stem. Use
unique output roots or post-process with region-aware naming rather than
assuming the flat output is collision-free. UAVid creates
`<sequence>/Labels`; huge-image writes directly under its output root.

**RGB mask looks like the wrong classes**

Do not reuse the LoveDA palette for PV/UAVid, and do not treat class ids as
RGB values. `--rgb` affects only tile evaluators; `-d` selects huge-image
mapping. Compare a known synthetic id mask with the tables in
[output formats](output-formats.md), remembering OpenCV BGR conversion.
A wrong mapping can still create valid-looking PNG files.

**All RGB pixels are black or an unexpected zero color appears**

The writer initializes a zero array and assigns only known class ids. Inspect
`np.unique` on the indexed predictions and compare the maximum id to
`num_classes - 1`; a stray id often means a class-head/config mismatch or an
unsupported mapping. Re-run indexed tile evaluation before attempting RGB
conversion.

## Shape, memory, and workflow failures

**`pre_image shape ...` versus `gt_image shape ...` assertion**

For tile evaluation, the model prediction must have the same height/width as
the dataset mask after transforms. Check that the config's test transform and
model input size agree with the prepared patch size; do not resize masks with
bilinear interpolation.

**Huge/UAVid assertion or broadcast error after stitching**

The scripts create a padded grid and expect each prediction to be exactly
`(patch-height, patch-width)`. Verify `-ph/-pw` are positive and match the
model's supported input shape, that the DataLoader does not reorder/drop tiles,
and that the checkpoint returns one mask per input tile. For an original
shape `(H,W)` the final crop must be exactly `(H,W)`; check the
bottom/right-padding case with the bundled `--check-padding` self-test. Never
crop from the top/left or trim by an assumed fixed amount.

**CUDA out-of-memory**

Reduce `-b` first (the default is 2), then reduce patch height/width only if the
selected model/config supports that input size. TTA multiplies work and memory;
prove base inference before enabling `lr` or `d4`. A smaller patch can change
model behavior and should be recorded, not silently treated as equivalent.

**Run is slow or appears stuck**

TTA, multiscale models, four DataLoader workers, and multiprocessing image
writers all add overhead. Check GPU utilization and disk space, then use a
small input subset, `-t` omitted, and `-b 1` to isolate the stage. Full real
inference is data/checkpoint dependent and intentionally not part of the
checkout's fast verification.

## Verification boundaries

Safe checks are parser `--help`, the dependency-free input validator, palette
and padding synthetic cases, and static config inspection. Full metrics,
checkpoint loading, RGB output, and CUDA inference remain external-data and
checkpoint dependent. Record skipped expensive runs explicitly instead of
converting a skip into a pass.
