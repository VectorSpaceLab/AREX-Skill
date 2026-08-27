# Evaluation notes

## Inputs
The evaluator takes two `.npz` files:
- a reference batch, and
- a sample batch.

### Sample batch requirements
- Must contain `arr_0`.
- `arr_0` should be an NHWC array of `uint8` RGB images.
- The common shape is `[50000, H, W, 3]`.

### Reference batch requirements
- May contain precomputed statistics (`mu`, `sigma`, `mu_s`, `sigma_s`).
- May also be a raw reference image batch.

## Packaging helper
Use `scripts/sample_c2i_ddp_pack_npz.py` when you have a folder of numbered PNGs.

Expected folder shape:
- either `sample_dir/000000.png`, `sample_dir/000001.png`, ...
- or `sample_dir/images/000000.png`, `sample_dir/images/000001.png`, ... when the sample batch already has an `images/` subfolder
- filenames are zero-padded six-digit numbers

The helper writes `sample_dir.npz` by default and places the packed images under `arr_0`.

## Evaluator behavior
- `evaluations/c2i/evaluator.py` computes IS, FID, sFID, precision, and recall.
- It downloads the InceptionV3 graph into the current working directory if the file is missing.
- The script can be slow on first run because TensorFlow warms up and the graph may need to be cached.

## Practical checks
- If the evaluator says the sample batch is missing `arr_0`, repackage the folder.
- If it says the reference batch is missing, confirm the path points to the ImageNet reference `.npz`.
- If the evaluator fails before reading the file, check TensorFlow, SciPy, and NumPy compatibility first.
