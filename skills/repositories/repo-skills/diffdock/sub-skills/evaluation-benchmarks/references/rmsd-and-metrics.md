# RMSD And Metrics

DiffDock benchmark evaluation records per-sample arrays and printed aggregate metrics. Interpret results by separating raw pose quality, confidence-ranked pose quality, GNINA-refined pose quality, and failure sentinels.

## Pose-Level RMSD Calculation

For each benchmark complex, `evaluate.py` samples `N = --samples_per_complex` ligand poses. It compares each sampled pose to one or more ground-truth ligand positions, removes hydrogens, and records the minimum RMSD over available ground-truth poses.

RMSD path:

1. Predicted ligand coordinates are collected for all samples.
2. Ground-truth ligand coordinates are centered by the receptor's original center.
3. Hydrogens are filtered from ligand coordinates.
4. DiffDock attempts symmetry-corrected RMSD through `get_symmetry_rmsd`.
5. If symmetry correction fails, it falls back to plain coordinate RMSD.
6. When multiple ground-truth poses exist, such as MOAD/PoseBusters alternatives, it takes the minimum RMSD across those ground truths.

Important caveats:

- RMSDs are computed without hydrogens included in the loss/reporting path.
- A failure after all retry attempts appends `10000` sentinel values for RMSD, centroid distance, and self-distance.
- `--samples_per_complex` controls whether top5/top10 metrics can be computed.
- `--no_model` returns randomized or seed conformers without running the score model; do not compare those numbers to normal benchmark results.

## Saved Arrays

Evaluation writes `.npy` arrays to `--out_dir`. The main arrays are:

| File | Meaning | Shape expectation |
| --- | --- | --- |
| `rmsds.npy` | RMSD for every sampled pose per complex. | approximately `(num_complexes, samples_per_complex)` |
| `centroid_distances.npy` | Ligand centroid distance for every sampled pose per complex. | approximately `(num_complexes, samples_per_complex)` |
| `confidences.npy` | Confidence model score for every sampled pose; empty or missing meaningful values when no confidence model is loaded. | approximately `(num_complexes, samples_per_complex)` |
| `min_self_distances.npy` | Minimum intra-ligand atom distance per sampled pose, used for self-intersection fractions. | approximately `(num_complexes, samples_per_complex)` |
| `run_times.npy` | Sampling runtime measurements. | one value per successfully timed complex |
| `complex_names.npy` | Complex ids included in the metric arrays. | one value per reported complex |
| `gnina_rmsds.npy` | RMSDs after GNINA minimization/full docking, when `--gnina_minimize` is enabled. | `(num_complexes, gnina_poses_to_optimize)` |
| `gnina_score.npy` | GNINA CNN scores read from minimized/docked SDF output, when enabled. | `(num_complexes, gnina_poses_to_optimize)` |

The script also saves `no_overlap_*.npy` variants only when the internal no-receptor-overlap mask is populated. In the current code path that mask is initialized empty, so no-overlap outputs may be absent.

## Printed Aggregate Metrics

The performance dictionary printed at the end includes:

| Metric family | Meaning |
| --- | --- |
| `run_times_mean`, `run_times_std` | Runtime summary over recorded complexes. |
| `mean_rmsd` | Mean over the full RMSD matrix, not only top-ranked poses. |
| `rmsds_below_2`, `rmsds_below_5` | Percent of all sampled poses under 2 Å or 5 Å RMSD. |
| `min_rmsds_below_2`, `min_rmsds_below_5` | Percent of complexes where at least one sampled pose is under threshold. |
| `rmsds_percentile_25/50/75` | Percentiles over all sampled RMSDs. |
| `mean_centroid`, `centroid_below_2`, `centroid_below_5` | Same style for ligand centroid distances. |
| `top5_*`, `top10_*` | Best RMSD among the first 5 or 10 samples per complex; only present when `samples_per_complex >= 5` or `>= 10`. |
| `*_self_intersect_fraction` | Percent of selected poses with minimum intra-ligand atom distance below `0.4`. |
| `filtered_*` | Metrics after ranking poses by confidence score and taking the top confidence pose or top confidence subset. |
| `gnina_*` | Metrics after GNINA minimization/full docking, when enabled. |

## Confidence Score Caveats

The confidence model is optional. When `--confidence_model_dir` is present, evaluation uses confidence scores to reorder generated samples from highest to lowest before reporting confidence-filtered metrics.

Caveats:

- A high confidence score is a ranking signal, not a binding affinity or calibrated probability by itself.
- When the confidence model has multi-bin RMSD classification output, evaluation uses the first column for ranking.
- NaN confidence values are replaced with `-1e-6` before sorting.
- If the confidence dataset lacks a complex and the confidence model cannot reuse the score-model cache, evaluation skips that complex and prints a skip message.
- `filtered_rmsds_below_*` answers "how good is the top-confidence pose?"; `min_rmsds_below_*` answers "did any sampled pose succeed?" These can diverge sharply.

## GNINA Metrics

With `--gnina_minimize`, DiffDock reorders positions by confidence when confidence is available, takes the first `--gnina_poses_to_optimize` positions, writes predicted ligand SDFs, invokes GNINA, reads the GNINA pose and `CNNscore`, then recomputes RMSD against ground truth.

GNINA outputs:

- `gnina_rmsds.npy`: RMSD after GNINA minimization or docking.
- `gnina_score.npy`: parsed `CNNscore` values from GNINA SDF output.
- `gnina_metrics.pkl`: only when `--save_gnina_metrics` is enabled; intended to map complex names to GNINA metrics for all samples.
- `gnina_logs/`: GNINA stdout/stderr logs under the output directory when the log directory exists.

Caveats:

- GNINA is run as an external shell command, not as a Python library.
- If GNINA output cannot be read, DiffDock prints an error, reuses the original DiffDock pose, and assigns score `0`.
- `gnina_filtered_rmsds_below_*` ranks GNINA poses by GNINA score, not DiffDock confidence.
- GNINA full docking uses `--autobox_ligand` and `--autobox_add`; minimization uses the predicted ligand as input with `--minimize`.
- A run can produce normal DiffDock RMSD arrays even when GNINA failed; inspect scores/logs before interpreting GNINA metrics.

## Vendored spyrmsd CLI

DiffDock vendors `spyrmsd` for symmetry-corrected RMSD calculations. The CLI entry point is:

```bash
python -m spyrmsd REFERENCE MOLECULE [MOLECULE ...] [--minimize] [--center] [--hydrogens] [--nosymm]
```

CLI arguments:

| Argument | Meaning |
| --- | --- |
| `reference` | Reference molecule file. |
| `molecules` | One or more molecule files to compare against the reference. |
| `-m`, `--minimize` | Fit/minimize RMSD using the QCP method. |
| `-c`, `--center` | Center molecules at the origin. |
| `--hydrogens` | Keep hydrogen atoms; by default the wrapper strips hydrogens. |
| `-n`, `--nosymm` | Disable graph-isomorphism symmetry correction. |

Standalone CLI dependencies:

- Importing the CLI requires Python dependencies such as NumPy.
- Loading molecule files requires either OpenBabel or RDKit support in the environment.
- If neither OpenBabel nor RDKit is importable, the CLI raises an import error before computing RMSD.

Use `scripts/inspect_spyrmsd_cli.py` to check CLI help or construct a command without requiring benchmark data.

## spyrmsd Python API Surface

Useful function signatures from the vendored package:

```python
spyrmsd.rmsd.rmsd(coords1, coords2, atomicn1, atomicn2, center=False, minimize=False, atol=1e-9)
spyrmsd.rmsd.symmrmsd(coordsref, coords, apropsref, aprops, amref, am, center=False, minimize=False, cache=True, atol=1e-9, return_permutation=False)
spyrmsd.rmsd.rmsdwrapper(molref, mols, symmetry=True, center=False, minimize=False, strip=True, cache=True)
spyrmsd.io.loadmol(fname, adjacency=True)
spyrmsd.io.loadallmols(fname, adjacency=True)
```

DiffDock's helper wraps `symmrmsd` by converting RDKit molecules to `spyrmsd.molecule.Molecule`, passing atomic numbers and adjacency matrices, and applying a 10-second alarm timeout. If this path times out or fails, evaluation falls back to plain RMSD and prints the exception.
