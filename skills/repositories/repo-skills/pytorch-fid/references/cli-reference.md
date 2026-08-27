# CLI Reference

`pytorch-fid` exposes the same command through the console script and module
entry point:

```bash
pytorch-fid PATH_A PATH_B [OPTIONS]
python -m pytorch_fid PATH_A PATH_B [OPTIONS]
```

Prefer `python -m pytorch_fid` when console scripts may not be on `PATH`.

## Installation and import check

Install the public package in a suitable Python environment:

```bash
pip install pytorch-fid
```

Then run the bundled safe probe from this skill directory:

```bash
python scripts/check_pytorch_fid_env.py
```

The probe does not construct `InceptionV3`, download weights, or read image
inputs.

## Positional paths

The CLI takes exactly two positional paths unless `--save-stats` is used.
Each normal comparison path can be:

- an image directory containing supported image files; or
- a `.npz` statistics file with `mu` and `sigma` arrays.

Common combinations:

```bash
# Compute statistics for both directories, then report FID.
python -m pytorch_fid real_images generated_images

# Compare generated images against precomputed reference stats.
python -m pytorch_fid generated_images reference_stats.npz

# Compare two saved statistics files.
python -m pytorch_fid reference_a.npz reference_b.npz
```

Validate inputs first when automating or diagnosing failures:

```bash
python scripts/validate_fid_inputs.py real_images generated_images --expected-dims 2048
python scripts/inspect_stats_npz.py reference_stats.npz
```

## Save-statistics mode

`--save-stats` changes the command shape to one input dataset directory and one
output `.npz` path:

```bash
python -m pytorch_fid --save-stats DATASET_DIR OUTPUT_STATS.npz
```

The output file stores activation mean/covariance under keys `mu` and `sigma`.
It must be regenerated for a different feature dimension. Do not reuse `2048`
stats for a `768`, `192`, or `64` comparison.

Avoid overwriting important reference stats accidentally. If the output path
already exists, choose a new filename unless replacement is intentional.

## Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--batch-size N` | `50` | Number of images per forward pass. Lower it for CPU memory pressure or CUDA OOM. |
| `--num-workers N` | `min(8, num_cpus)` | DataLoader worker count. Use `0` or `1` for debugging, restricted platforms, or reproducible small runs. |
| `--device DEVICE` | auto parser default, effectively CPU when not set | Torch device string such as `cpu`, `cuda`, or `cuda:0`. Verify CUDA availability first. |
| `--dims {64,192,768,2048}` | `2048` | Inception feature dimension. Determines the selected output block. Scores across different dims are not comparable. |
| `--save-stats` | off | Store statistics for one dataset instead of printing a FID comparison. |

The accepted dimensions come from `InceptionV3.BLOCK_INDEX_BY_DIM`:

- `64` selects block index `0`;
- `192` selects block index `1`;
- `768` selects block index `2`;
- `2048` selects block index `3`.

## Expected output

Normal comparison prints a single FID line to standard output. The exact text can
vary by version, but the operative value is the reported floating-point FID
score. Lower scores indicate closer generated-image statistics to reference
image statistics under the chosen implementation and settings.

`--save-stats` writes the `.npz` file and does not represent a completed FID
comparison by itself.

## Gotchas

- First real FID computation may download FID Inception weights through PyTorch
  cache machinery. A no-network environment may need pre-populated cache.
- Empty directories and directories without supported extensions fail later in
  the run unless validated first.
- Image extensions are suffix-filtered; supported suffixes are `bmp`, `jpg`,
  `jpeg`, `pgm`, `png`, `ppm`, `tif`, `tiff`, and `webp`.
- `.npz` files must contain `mu` and `sigma`; the dimension must match `--dims`.
- CUDA acceleration is optional. If CUDA is unavailable, use CPU or select a
  valid CUDA device after checking `torch.cuda.is_available()`.
- For torch builds incompatible with NumPy 2, use NumPy 1.x (`numpy<2`) to avoid
  ABI warnings or import/runtime failure.
- FID values from this PyTorch implementation are not guaranteed to match the
  official TensorFlow implementation exactly.

See [`data-formats.md`](data-formats.md) for input validation details and
[`troubleshooting.md`](troubleshooting.md) for recovery steps.
