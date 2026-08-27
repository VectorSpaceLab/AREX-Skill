# Tracking And Segmentation Workflows

These recipes are for future agents planning Dipy tracking and segmentation tasks without relying on original repo examples or downloads. Replace synthetic probes with user data only after validating shapes, affines, spaces, and expected output scale.

## 1. Local Tracking From Model Outputs

1. Prepare directions outside this sub-skill:
   - Use `../../reconstruction-models/` to fit diffusion models, compute peaks, generate SH coefficients, or create/load PAM files.
   - For CLI tracking, `dipy_track` expects a PAM file, stopping image, and seed image.
2. Validate spatial inputs:
   - Seed and stopping masks must be 3D voxel grids in the same reference space.
   - `LocalTracking` needs a `(4, 4)` non-shearing affine and a positive `step_size`.
   - `seeds_from_mask(seed_mask, affine, density=...)` returns seed coordinates in the affine point space.
3. Choose stopping:
   - Use `BinaryStoppingCriterion` for binary tracking support masks.
   - Use `ThresholdStoppingCriterion(metric_map, threshold)` for FA-like scalar stopping.
   - Use `ActStoppingCriterion` or `CmcStoppingCriterion` for aligned WM/GM/CSF PVE maps.
4. Bound the run:
   - Set `random_seed` for stochastic helpers.
   - Keep `minlen`, `maxlen`, and `step_size` consistent with coordinate units.
   - Use `return_all=True` during diagnosis and `return_all=False` when endpoint validity matters.
5. Validate before saving:
   - Count seeds and streamlines.
   - Check all streamline lengths are positive and plausible.
   - Check coordinate min/max against the intended image/reference.
   - Route saving/reference-image details to `../../io-data/`.

## 2. Particle Filtering Tracking

1. Prepare PAM/SH directions and WM/GM/CSF PVE maps in the same grid.
2. Use `dipy_track_pft` for CLI runs or `ParticleFilteringTracking`/`pft_tracking` for code.
3. Confirm the stopping criterion is anatomical, not binary/threshold-only.
4. Keep `step_size`, `pft_back`, `pft_front`, `pft_count`, and voxel-size assumptions in the same units.
5. Probe a small seed ROI before whole-brain PFT; PFT can be slower and more memory intensive than deterministic tracking.

## 3. Streamline Manipulation And ROI Filtering

1. Wrap streamlines in `Streamlines` when APIs expect Dipy's streamline container.
2. Use `set_number_of_points` before profile, shape, or clustering workflows that need equal nodes.
3. Use `target`/`target_line_based` only after confirming the streamline coordinates map inside the ROI mask through the provided affine.
4. Use `density_map` and `length` for numeric sanity checks before optional rendering.
5. Use `transform_streamlines` for known transforms; if transforms must be estimated, route to `../../registration-alignment/`.
6. Use `compress_streamlines` after, not before, proving ROI and tractometry results remain stable enough for the task.

## 4. QuickBundles And Cluster Summaries

1. Start with a small `Streamlines` object containing non-degenerate `(points, 3)` arrays.
2. Choose threshold in the same units as the streamline coordinates; for RASMM tractograms this is usually millimeters.
3. Use `QuickBundles(threshold)` and default `metric='MDF_12points'` for first-pass clustering.
4. For larger tractograms, use `QuickBundlesX` or `qbx_and_merge` with a threshold ladder such as coarse-to-fine millimeter values.
5. Validate `len(clusters)`, sorted cluster sizes, centroids, and representative indices.
6. If one giant cluster appears, lower the threshold; if every streamline is isolated, raise the threshold or resample/orient consistently.

## 5. RecoBundles And LabelsBundles

1. Confirm the subject tractogram and model bundles are roughly in the same coordinate space and units.
2. Construct `RecoBundles(streamlines, greater_than=..., less_than=..., clust_thr=..., nb_pts=...)` with length filters appropriate for the coordinate units.
3. Run `recognize(model_bundle, model_clust_thr, reduction_thr=..., pruning_thr=..., slr=...)` with conservative thresholds first.
4. Keep `slr_select` small for probes and expand only after labels and recognized bundle size are plausible.
5. Use `refine` only after first-pass recognition returns enough streamlines to refine.
6. Validate recognized bundle count, labels indexing the original tractogram, bundle adjacency/BMD metrics, and coordinate range.
7. Use `dipy_labelsbundles` to recover original/native-space bundles from saved labels when RecoBundles output is in model/common space.

## 6. Brain Masking And Tissue Classification

1. For classic masking, prefer `median_otsu` or `dipy_median_otsu`:
   - 3D images can omit `vol_idx`.
   - 4D images require `vol_idx`, or CLI b-values can select b0 volumes.
   - Prefer `dilate` and `finalize_mask=True` for cleanup.
   - Avoid deprecated `autocrop` unless a shape-changing output is explicitly desired.
2. For `dipy_brain_mask`, choose `--method median_otsu` when optional neural-network backends are missing or not desired.
3. For HMRF tissue classification, pick `nclasses`, `beta`, and iteration/tolerance controls on a small image first; remember the implementation adds a background class internally.
4. For DAM tissue classification, provide b-values and verify diffusion-shell assumptions.
5. Validate all masks and PVE maps by shape, dtype/value range, nonzero count, and spatial overlap with seed/stopping regions.

## 7. AFQ And BUAN Handoff

1. For a single along-tract profile, use `afq_profile(data, bundle, affine, n_points=...)`:
   - Ensure `len(bundle) > 0`.
   - Orient streamlines consistently with `orient_by_streamline` or pass `orient_by`.
   - Validate output length equals `n_points`.
2. For BUAN profiles, prepare model bundles, registered/common-space bundles, original/native bundles, metric volumes, and consistent naming.
3. Use `dipy_buan_profiles` for profile artifacts; confirm whether the subject folder is single-subject or patient/control group layout.
4. Use `dipy_buan_shapes` for shape similarity and `dipy_buan_lmm` for group model outputs.
5. Treat plots/statistical model summaries as optional surfaces if matplotlib, pandas, statsmodels, or related packages are absent.

## 8. CLI Planning Patterns

- `dipy_track`: start with `--tracking_method det`, a low seed density, bounded lengths, and fixed `--random_seed`; only then try probabilistic/closest-peaks/PTT variants.
- `dipy_track_pft`: verify WM/GM/CSF maps and seed mask with image metadata before launching; PFT parameters are spatial-unit sensitive.
- `dipy_cluster_streamlines`: use `--method quickbundles` for simple probes and `qbx_and_merge` for larger bundles.
- `dipy_recobundles`: start with a known model bundle and small SLR settings; use `--refine` only after the first pass returns labels.
- `dipy_median_otsu` and `dipy_brain_mask`: always specify how 4D volumes choose b0/masking volumes.
- `dipy_buan_*`: check directory layout and dependencies before expecting downstream plots or group statistics.

## 9. Built-In Smoke And Hard Cases

- Run `scripts/dipy_streamline_smoke.py` to verify the installed Dipy can construct streamlines, cluster two synthetic groups, generate deterministic seeds, and instantiate binary/threshold stopping criteria.
- Hard case: tiny deterministic tracking setup from synthetic peaks or initial directions plus a mask, where the agent must explain why seeds, affine, step size, and stopping grid agree before accepting streamline counts.
- Hard case: cluster streamlines, then explain reference image, coordinate space, origin, and label/recognized-bundle handoff before any save operation; route tractogram serialization to `../../io-data/`.
