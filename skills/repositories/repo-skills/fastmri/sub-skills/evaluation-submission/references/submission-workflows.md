# Submission workflows

This reference gives safe, self-contained workflows for producing and checking fastMRI leaderboard-style reconstruction directories.

## Prepare model predictions

When a model returns a mapping of filenames to real-valued reconstruction arrays, save the mapping with fastMRI's helper:

```python
from pathlib import Path
import fastmri

fastmri.save_reconstructions(reconstructions, Path("predictions"))
```

The helper creates the output directory and writes each array as dataset `reconstruction`. Keep filenames aligned with the original target/test volume names unless a specific v2 conversion step is required.

## Validate predictions before metrics or packaging

Use the bundled validator first:

```bash
python scripts/validate_reconstructions.py \
  --predictions-path predictions \
  --target-path targets \
  --challenge multicoil
```

The validator checks that each prediction `.h5` contains `reconstruction`, can be read as an array, and, when targets are supplied, has a matching target filename and the challenge-appropriate target key. It also reports how many files would survive optional acquisition or acceleration filters.

For upload-style checks without targets:

```bash
python scripts/validate_reconstructions.py --predictions-path predictions --require-v2
```

`--require-v2` is useful when a destination expects knee v2-style filenames.

## Run local metrics

With target files available:

```bash
python -m fastmri.evaluate \
  --target-path targets \
  --predictions-path predictions \
  --challenge multicoil
```

Add filters only when they match target attributes:

```bash
python -m fastmri.evaluate \
  --target-path targets \
  --predictions-path predictions \
  --challenge multicoil \
  --acceleration 4 \
  --acquisition CORPD_FBK
```

The evaluation command prints means and two-standard-deviation bands for MSE, NMSE, PSNR, and SSIM. If filters skip every target file, do not treat the output as a valid score; rerun validation with the same filters to confirm file coverage.

## Convert filenames to v2

For public knee leaderboard-style filenames, convert after writing predictions and before packaging:

```python
from pathlib import Path
from fastmri import convert_fnames_to_v2

convert_fnames_to_v2(Path("predictions"))
```

The conversion renames `file1000.h5` to `file1000_v2.h5` and leaves existing `_v2.h5` names unchanged. It raises `ValueError` if the directory does not exist.

## Build a zero-filled baseline

Use the bundled script rather than the source example path:

```bash
python scripts/zero_filled_reconstruction.py \
  --data-path kspace_data \
  --output-path predictions_zero_filled \
  --challenge multicoil
```

The script reads `kspace` and `ismrmrd_header`, applies `fastmri.ifft2c`, crops using encoded matrix size from the header, applies `fastmri.complex_abs`, and applies `fastmri.rss(..., dim=1)` for multicoil data. Outputs are written with `fastmri.save_reconstructions`, so the prediction key is `reconstruction`.

If a header asks for a crop larger than the reconstructed image height, the script falls back to a square crop based on the available image height. This mirrors the zero-filled FLAIR 203 caveat: some brain files with `FLAIR_203` in the filename have known crop/header issues and were ignored for the original brain leaderboard.

## BART compressed-sensing caveat

The compressed-sensing baseline is reference-only for this skill. It depends on the external BART toolkit and environment variables such as `TOOLBOX_PATH` and `PYTHONPATH`, and it is not bundled as a runnable skill script. If a user asks for that baseline, explain the external dependency and prefer zero-filled or model-generated predictions unless they already have a working BART installation.

The BART README also notes that the 2020 Brain Challenge used equispaced masks, which are not supported by compressed-sensing theory, so CS is not a universal fastMRI baseline.

## Leaderboard availability caveat

The repository README states that the fastmri.org domain transfer left leaderboards unavailable until NYU rebuilds the site. Treat this skill as preparing, validating, and evaluating files locally. Do not guarantee that an upload endpoint is available.
