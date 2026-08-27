---
name: evaluation-submission
description: "Prepare fastMRI reconstructions for validation, metric evaluation,
  zero-filled baselines, v2 filename conversion, and leaderboard-style
  submissions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fastMRI evaluation-submission

Use this sub-skill when an agent needs to create, validate, rename, evaluate, or explain fastMRI reconstruction outputs for validation/test-style submission workflows.

Do not use this sub-skill for HDF5 dataset loading internals, low-level MRI tensor operators, or training loops; route those to [data-loading](../data-loading/SKILL.md), [mri-operators](../mri-operators/SKILL.md), or the training sub-skill instead.

## References and scripts

- [Evaluation reference](references/evaluation-reference.md): Use this for exact public APIs, metric definitions, challenge target keys, and evaluation crop behavior.
- [Submission workflows](references/submission-workflows.md): Use this for end-to-end output preparation, zero-filled baselines, metric runs, v2 filename conversion, and BART caveats.
- [Troubleshooting](references/troubleshooting.md): Use this to diagnose missing datasets, filename/key mismatches, empty filters, crop issues, unavailable leaderboards, and optional BART setup failures.
- [Zero-filled reconstruction script](scripts/zero_filled_reconstruction.py): Use this bundled baseline script to turn fastMRI k-space HDF5 files into `reconstruction` prediction files without depending on repository example paths.
- [Validation script](scripts/validate_reconstructions.py): Use this before metrics or packaging to check prediction filenames, HDF5 keys, target compatibility, optional filters, and v2 suffix expectations.

## Critical facts

- `fastmri.save_reconstructions(reconstructions, out_dir)` writes one `.h5` per dictionary key and stores the array under dataset key `reconstruction`.
- `fastmri.convert_fnames_to_v2(path)` renames `.h5` files missing the `_v2.h5` suffix and raises `ValueError` if the directory path does not exist.
- Metric evaluation expects target files and prediction files to share filenames; prediction files must contain dataset `reconstruction`.
- `--challenge multicoil` uses target key `reconstruction_rss`; `--challenge singlecoil` uses target key `reconstruction_esc`.
- The evaluation path center-crops both target and reconstruction to the square target width before computing MSE, NMSE, PSNR, and SSIM.
- The public fastMRI leaderboard site is unavailable in this checkout's README notice, so prepare and validate outputs but do not promise upload availability.

## Minimal commands

```bash
python scripts/validate_reconstructions.py --predictions-path PREDICTIONS --target-path TARGETS --challenge multicoil
python -m fastmri.evaluate --target-path TARGETS --predictions-path PREDICTIONS --challenge multicoil
python scripts/zero_filled_reconstruction.py --data-path KSPACE_DATA --output-path PREDICTIONS --challenge multicoil
```

For public knee v2-style filenames after writing predictions:

```python
from pathlib import Path
from fastmri import convert_fnames_to_v2
convert_fnames_to_v2(Path("PREDICTIONS"))
```
