# Data Formats

Use this reference before running CLI/API calls that construct Inception models.
Most expensive or confusing failures can be avoided by validating image
directories and `.npz` statistics first.

## Accepted input path types

A normal FID comparison takes two input paths. Each path may be either:

1. an image directory; or
2. a saved statistics `.npz` file.

`--save-stats` mode is different: the first path is an image directory and the
second path is an output `.npz` file that must not already exist.

## Image directories

Expected layout:

```text
images/
  sample_000001.png
  sample_000002.jpg
  sample_000003.webp
```

Important details:

- The package enumerates images directly in the input directory; do not rely on
  recursive discovery through nested class folders.
- Supported filename extensions are `bmp`, `jpg`, `jpeg`, `pgm`, `png`, `ppm`,
  `tif`, `tiff`, and `webp`.
- Use lowercase suffixes for portable behavior because source matching is by
  explicit extension patterns.
- Files are opened with Pillow and converted to RGB.
- Non-image files with supported suffixes will fail when Pillow tries to open
  them.
- Empty directories or directories without supported suffixes should be treated
  as invalid FID inputs.

Validation command:

```bash
python scripts/validate_fid_inputs.py images_a images_b --expected-dims 2048
```

The validator checks existence, directory status, supported extension counts,
and sample paths. It does not import torch, construct a model, or download
weights.

## `.npz` statistics files

Saved FID stats are NumPy archives with exactly the arrays needed for the
package's high-level stats-loading path:

- `mu`: activation mean vector;
- `sigma`: activation covariance matrix.

Expected shapes for feature dimension `D`:

- `mu.shape == (D,)`
- `sigma.shape == (D, D)`

Supported `D` values for package-generated stats are `64`, `192`, `768`, and
`2048`, matching the `--dims`/`InceptionV3.BLOCK_INDEX_BY_DIM` choices.

Inspect stats:

```bash
python scripts/inspect_stats_npz.py reference_stats.npz
python scripts/inspect_stats_npz.py reference_stats.npz --json
```

The inspection script reports:

- whether `mu` and `sigma` keys are present;
- shapes, inferred dimension, and dtype;
- finite-value checks;
- covariance squareness;
- approximate symmetry of `sigma`;
- warnings when shape and dimension are inconsistent.

## Dimension compatibility

Before comparing two inputs, ensure the dimension used by each side is the same.
For two `.npz` files, this means both archives should have the same `mu` length
and `sigma` shape. For a directory-versus-`.npz` comparison, the CLI/API
`--dims` value must match the saved stats dimension.

Examples:

```bash
# Good: 2048-dimensional stats compared with a 2048-dimensional run.
python -m pytorch_fid generated_images reference_2048.npz --dims 2048

# Bad: 2048-dimensional stats reused with 768-dimensional features.
python -m pytorch_fid generated_images reference_2048.npz --dims 768
```

Validation command with an expected dimension:

```bash
python scripts/validate_fid_inputs.py generated_images reference_2048.npz --expected-dims 2048
```

## Covariance checks

A valid covariance matrix should be:

- two-dimensional;
- square;
- side length equal to `mu` length;
- finite;
- approximately symmetric.

The package's core FID function checks only some shape equality conditions at
calculation time. It is better to reject malformed stats before model creation.

For numerical edge cases, `calculate_frechet_distance` may add a small diagonal
offset when the covariance product is nearly singular. It may also raise a
`ValueError` if `scipy.linalg.sqrtm` produces a non-negligible imaginary
component.

## Save-statistics output contract

Create reusable stats with:

```bash
python -m pytorch_fid --save-stats DATASET_DIR reference_stats.npz --dims 2048
```

Operational rules:

- The input must be an existing image directory.
- The output file must not already exist; the package raises `RuntimeError` for
  an existing output path.
- Name files with the feature dimension when multiple dimensions are used, for
  example `train_2048_stats.npz` and `train_768_stats.npz`.
- Treat stats as implementation-specific: record package/version, feature
  dimension, source dataset, and preprocessing convention outside the archive.

## Validation-first checklist

Before an expensive FID run:

1. Run [`scripts/check_pytorch_fid_env.py`](../scripts/check_pytorch_fid_env.py)
   to confirm imports and CLI availability.
2. Run [`scripts/validate_fid_inputs.py`](../scripts/validate_fid_inputs.py) on
   the two comparison inputs.
3. Run [`scripts/inspect_stats_npz.py`](../scripts/inspect_stats_npz.py) for any
   saved-statistics file whose provenance is uncertain.
4. Confirm the intended `--dims` value and ensure all saved stats were generated
   with that same value.
5. Confirm whether a first-run model-weight download is allowed or whether cache
   must already be populated.
6. Choose `--batch-size`, `--num-workers`, and `--device` conservatively for the
   available machine.
