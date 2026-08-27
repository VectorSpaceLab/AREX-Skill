# Workflows

Use these recipes for pytorch-fid operations. Each recipe starts with safe
validation before any Inception model construction or possible weight download.

## 1. Compute FID between two image directories

Use when both real/reference images and generated images are available as flat
image directories.

```bash
python scripts/check_pytorch_fid_env.py
python scripts/validate_fid_inputs.py real_images generated_images --expected-dims 2048
python -m pytorch_fid real_images generated_images --dims 2048 --batch-size 50
```

Adjustments:

- Add `--device cuda:0` only after confirming CUDA is available.
- Reduce `--batch-size` for CUDA OOM or CPU memory pressure.
- Set `--num-workers 0` or `1` when debugging platform/DataLoader issues.
- Use lower `--dims` only when faster non-2048 comparisons are intentionally
  desired and all compared scores use the same dimension.

## 2. Precompute reusable reference statistics

Use when the same reference dataset is compared against many generated runs.

```bash
python scripts/check_pytorch_fid_env.py
python scripts/validate_fid_inputs.py reference_images reference_images --expected-dims 2048
python -m pytorch_fid --save-stats reference_images reference_2048_stats.npz --dims 2048
python scripts/inspect_stats_npz.py reference_2048_stats.npz
```

Notes:

- `--save-stats` expects one input directory and one output `.npz` path.
- The package refuses to overwrite an existing output file.
- Include the feature dimension in the filename when keeping multiple stats
  files.
- Keep external provenance notes for dataset split, preprocessing, package
  version, and feature dimension.

## 3. Compare generated images against saved stats

Use after precomputing reference statistics.

```bash
python scripts/validate_fid_inputs.py generated_images reference_2048_stats.npz --expected-dims 2048
python -m pytorch_fid generated_images reference_2048_stats.npz --dims 2048 --batch-size 50
```

If the saved stats dimension is not known:

```bash
python scripts/inspect_stats_npz.py reference_2048_stats.npz
```

Then set `--dims` to the reported `mu` length if it is one of `64`, `192`,
`768`, or `2048`.

## 4. Compare two saved statistics files

Use when both sides have already been summarized.

```bash
python scripts/inspect_stats_npz.py stats_a.npz stats_b.npz
python scripts/validate_fid_inputs.py stats_a.npz stats_b.npz --expected-dims 2048
python -m pytorch_fid stats_a.npz stats_b.npz --dims 2048
```

This path still constructs the model in the high-level package function, even
though the statistics are already present. If model construction or weight cache
is a problem and the task only needs the numeric formula, use the lower-level
`calculate_frechet_distance` API after loading `mu`/`sigma` yourself.

## 5. Programmatic FID from paths

```python
from pytorch_fid.fid_score import calculate_fid_given_paths

fid_value = calculate_fid_given_paths(
    ["real_images", "generated_images"],
    batch_size=50,
    device="cpu",
    dims=2048,
    num_workers=1,
)
print(float(fid_value))
```

Add your own input validation before the call. The package verifies path
existence but does not provide the same detailed validation as the bundled
scripts.

## 6. Programmatic Frechet distance from saved arrays

Use when you already trust two stats files and want to avoid model construction.

```python
import numpy as np
from pytorch_fid.fid_score import calculate_frechet_distance

with np.load("stats_a.npz") as a, np.load("stats_b.npz") as b:
    fid_value = calculate_frechet_distance(a["mu"], a["sigma"], b["mu"], b["sigma"])
print(float(fid_value))
```

Validate the stats first with:

```bash
python scripts/inspect_stats_npz.py stats_a.npz stats_b.npz
```

## Choosing `--dims`

Default to `2048` unless the user has a reason to use a lower layer.

| Dims | Use when | Caution |
| --- | --- | --- |
| `2048` | Standard FID comparisons and most published workflows. | Slower and more memory-intensive than lower dims. |
| `768` | Faster exploratory checks where all runs use the same setting. | Not comparable to 2048-dimensional FID. |
| `192` | Very lightweight diagnostics. | Less standard as a quality metric. |
| `64` | Smoke tests or highly constrained environments. | Do not compare with standard FID numbers. |

Never mix dimensions within a leaderboard, experiment table, or regression
threshold.

## Choosing device and batch settings

CPU workflow:

```bash
python -m pytorch_fid real_images generated_images --device cpu --batch-size 16 --num-workers 1
```

CUDA workflow:

```bash
python scripts/check_pytorch_fid_env.py --json
python -m pytorch_fid real_images generated_images --device cuda:0 --batch-size 50
```

Guidance:

- Use CPU for small validation, deterministic troubleshooting, or machines
  without CUDA.
- Use CUDA for larger image sets when a compatible torch build and GPU are
  available.
- Reduce batch size before changing dimensions when memory fails.
- Lower `--num-workers` for shared systems, notebooks, Windows-style spawn
  issues, or file-handle pressure.

## Validation-first operation

Before any reported result:

1. Record the two input paths and their intended role.
2. Validate path existence, directory image counts, or `.npz` stats schema.
3. Confirm feature dimension and stats compatibility.
4. Confirm package version and environment compatibility.
5. Confirm first-run weight download/cache constraints.
6. Run the FID command or API.
7. Record command, dimension, device, batch size, package version, and stats
   provenance with the resulting score.

## Interpreting and reporting scores

Report FID values with enough context to make them reproducible:

```text
FID=12.34 using pytorch-fid 0.3.0, dims=2048, FID Inception weights,
reference=train_2048_stats.npz, generated=run_42_samples, device=cuda:0,
batch_size=50.
```

Do not compare scores across different FID implementations, feature dimensions,
preprocessing conventions, or reference-stat provenance.
