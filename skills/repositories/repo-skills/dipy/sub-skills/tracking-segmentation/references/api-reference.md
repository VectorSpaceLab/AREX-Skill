# Tracking And Segmentation API Reference

This reference summarizes Dipy runtime APIs for tractography, streamline manipulation, bundle clustering/segmentation, masking, tissue classification, AFQ, BUAN, and related CLIs. It assumes data is already local and routes file-format/reference handling to `../../io-data/`.

## Tracking Construction

| Need | Primary API | Key inputs | Notes |
| --- | --- | --- | --- |
| Local tractography from a direction getter | `dipy.tracking.local_tracking.LocalTracking(direction_getter, stopping_criterion, seeds, affine, step_size, *, max_cross=None, maxlen=500, minlen=2, fixedstep=True, return_all=True, random_seed=None, save_seeds=False, unidirectional=False, randomize_forward_direction=False, initial_directions=None)` | Direction getter, stopping criterion, `(N, 3)` seeds, `(4, 4)` affine, positive `step_size` | Iterable of streamlines. Use `random_seed` for reproducibility and `save_seeds=True` when seed provenance matters. EuDX-style direction getter objects are deprecated for this low-level API; prefer current tracker helpers or PAM/SH-based flows. |
| Particle-filtering tracking | `dipy.tracking.local_tracking.ParticleFilteringTracking(...)` | Direction getter, anatomical stopping criterion, seeds, affine, step size, PFT back/front distances, particle count | Requires an `AnatomicalStoppingCriterion`; validate PVE maps, affine, and spatial units before full runs. |
| High-level tracker helpers | `dipy.tracking.tracker.deterministic_tracking`, `probabilistic_tracking`, `closestpeak_tracking`, `eudx_tracking`, `ptt_tracking`, `pft_tracking` | Seeds, stopping criterion, affine, one direction source such as `sh`, `pam`, or `sf`, plus method controls | Useful when starting from PAM/SH-like reconstruction outputs. Route direction/model creation to `../../reconstruction-models/`. |
| Deterministic seeds | `dipy.tracking.utils.seeds_from_mask(mask, affine, *, density=(1, 1, 1))` | 3D binary mask, affine, integer density scalar or length-3 density | Returns seed coordinates in affine point space; scalar density `2` yields 8 seeds per nonzero voxel. |
| Random seeds | `dipy.tracking.utils.random_seeds_from_mask(mask, affine, *, seeds_count=1, seed_count_per_voxel=True, random_seed=None)` | 3D binary mask, affine, count controls | Use only when stochastic seeding is intentional; set `random_seed` for repeatable probes. |

## Direction And Stopping Contracts

| Surface | Use when | Construction notes | Checks |
| --- | --- | --- | --- |
| `BinaryStoppingCriterion(mask)` | Continue inside a binary tracking mask and end outside it | Nonzero mask values become tracking voxels | Mask must be 3D and aligned to seed/stopping affine. |
| `ThresholdStoppingCriterion(metric_map, threshold)` | Continue while a scalar map, often FA-like support, is above threshold | Samples `metric_map` by interpolation; out-of-bounds points terminate as outside image | Map shape and affine must match the tracking grid; tune threshold on a small seed region. |
| `ActStoppingCriterion.from_pve(wm_map, gm_map, csf_map)` | ACT-style anatomical endpoint/invalid-point logic | Uses gray matter/background as include and CSF as exclude | WM/GM/CSF arrays must share shape, affine, and plausible value ranges. |
| `CmcStoppingCriterion.from_pve(wm_map, gm_map, csf_map, step_size=..., average_voxel_size=...)` | CMC/PFT workflows | Step size and average voxel size must be in compatible units | Use with PFT when tissue maps are trustworthy and aligned. |
| Direction getters and PAM/SH inputs | Tracking directions already computed by reconstruction | Current installed facts place `peaks_from_model` at `dipy.direction.peaks.peaks_from_model`, not `dipy.reconst.peaks` | Use `../../reconstruction-models/` for model fitting, peak creation, and PAM serialization. |

## Streamline Containers And Manipulation

| Need | API | Notes |
| --- | --- | --- |
| Hold variable-length streamlines | `dipy.tracking.streamline.Streamlines(iterable=None, buffer_size=4)` | Sequence-like container for `(points, 3)` arrays; common input to clustering and tractometry. |
| Resample streamlines | `dipy.tracking.streamline.set_number_of_points(streamlines, nb_points)` | Required by many clustering, shape, and profile workflows that need equal node counts. |
| Transform known coordinates | `dipy.tracking.streamline.transform_streamlines(streamlines, mat, *, in_place=False)` | Use for applying an already-known transform. Route transform estimation to `../../registration-alignment/`. |
| Filter by ROI | `dipy.tracking.utils.target(streamlines, affine, target_mask, *, include=True)` and `target_line_based(...)` | Raises when points map outside the target mask; line-based variant is safer for compressed streamlines. |
| Compute density and lengths | `dipy.tracking.utils.density_map`, `dipy.tracking.utils.length`, `dipy.tracking.metrics.length` | Use as quick numeric checks before saving or visualization. |
| Orient/sample tract profiles | `dipy.tracking.streamline.orient_by_streamline`, `values_from_volume` | Useful before `afq_profile`; orientation consistency strongly affects profile interpretation. |
| Compress streamlines | `dipy.tracking.streamline.compress_streamlines(streamlines, tol_error=0.01, max_segment_length=10)` | Validate downstream ROI filtering and tractometry after compression. |

## Clustering And Bundle Segmentation

| Task | API | Parameters that matter | Notes |
| --- | --- | --- | --- |
| Flat clustering | `dipy.segment.clustering.QuickBundles(threshold, *, metric='MDF_12points', max_nb_clusters=None)` | `threshold` in streamline coordinate units; default metric resamples to 12 points | `cluster(streamlines)` returns clusters with centroids, indices, and sizes. |
| Hierarchical clustering | `dipy.segment.clustering.QuickBundlesX(thresholds, *, metric='MDF_12points')` and `qbx_and_merge` | Threshold ladder, node count, ordering/subsampling | Use for larger tractograms or as a RecoBundles pre-clustering strategy. |
| Bundle recognition | `dipy.segment.bundles.RecoBundles(streamlines, *, greater_than=50, less_than=1000000, cluster_map=None, clust_thr=15, nb_pts=20, rng=None, verbose=False)` | Length filters, clustering threshold, number of points, RNG | Subject streamlines and model bundle must already be roughly in the same space; thresholds assume millimeter-like coordinates. |
| Recognition/refinement | `RecoBundles.recognize(...)`, `refine(...)`, `evaluate_results(...)` | `model_clust_thr`, `reduction_thr`, `pruning_thr`, `slr`, `slr_x0`, `slr_bounds`, `slr_select` | Start with conservative thresholds and smaller `slr_select`; inspect labels and recognized streamline count before scaling. |
| Bundle shape similarity | `dipy.segment.bundles.bundle_shape_similarity`, `ba_analysis` | Threshold and clustering settings | Useful for comparing recognized bundles across subjects or against model/expert bundles. |

## Masking And Tissue Segmentation

| Need | API | Notes |
| --- | --- | --- |
| Classic brain mask | `dipy.segment.mask.median_otsu(input_volume, *, vol_idx=None, median_radius=4, numpass=4, autocrop=False, dilate=None, finalize_mask=False)` | For 4D input, pass `vol_idx`; prefer `dilate`/`finalize_mask=True` over deprecated `autocrop`. |
| Mask application and cleanup | `applymask`, `bounding_box`, `crop`, `remove_holes_and_islands` | Validate mask shape, nonzero count, and overlap before using it as seed/stopping support. |
| HMRF tissue classification | `dipy.segment.tissue.TissueClassifierHMRF(*, save_history=False, verbose=True)` then `.classify(image, nclasses, beta, *, tolerance=1e-05, max_iter=100, min_var=1e-6)` | Returns initial segmentation, final segmentation, and PVE maps. It internally adds a background class. |
| DAM tissue classification | `dipy.segment.tissue.dam_classifier` and `dipy_classify_tissue --method dam` | Requires diffusion signal and b-values; use when the directional-average method is appropriate. |
| Neural-network brain mask | `dipy_brain_mask --method synthseg|evac` | Optional PyTorch/model-weight surface; base/minimal installs may fall back to `median_otsu` or fail to load neural backends. |

## AFQ, BUAN, And Tractometry

| Task | API/CLI | Contract |
| --- | --- | --- |
| Along-bundle scalar profile | `dipy.stats.analysis.afq_profile(data, bundle, affine, *, n_points=100, profile_stat=np.average, orient_by=None, weights=None, **weights_kwarg)` | Bundle must be non-empty. Use `orient_by` or pre-orient streamlines when direction matters. Output length equals `n_points`. |
| Bundle profile internals | `dipy.stats.analysis.buan_profile`, `assignment_map`, profile helpers | Inputs are model, registered, original/native bundle, metric volume, and affine-like references. |
| Group/profile workflow | `dipy_buan_profiles` | Uses model bundles plus subject folders; supports single-subject and patient/control group directory layouts. |
| Shape analysis | `dipy_buan_shapes` | Computes bundle-shape similarity matrices from recognized bundles. |
| Linear mixed models | `dipy_buan_lmm` | Consumes BUAN profile HDF5 outputs; plotting/statistics dependencies are optional environment concerns. |

## Owned CLI Commands

| CLI | Flow class | Typical purpose | Key inputs |
| --- | --- | --- | --- |
| `dipy_track` | `LocalFiberTrackingPAMFlow` | Local tracking from saved PAM plus stopping and seeding images | PAM file, stopping image, seed mask; `--tracking_method` supports `eudx`, `det`/`deterministic`, `prob`/`probabilistic`, `cp`/`closestpeaks`, and `ptt`. |
| `dipy_track_pft` | `PFTrackingPAMFlow` | Particle-filtering tracking from PAM and tissue maps | PAM, WM/GM/CSF PVE maps, seed mask, PFT parameters. |
| `dipy_cluster_streamlines` | `ClusterStreamlinesFlow` | Cluster local tractograms | Tractogram, method `quickbundles`, `qbx_and_merge`, or `faststreamlines`, thresholds, node count. |
| `dipy_recobundles` | `RecoBundlesFlow` | Recognize model bundles in a subject tractogram | Subject tractogram, model bundle files, thresholds, SLR/refine options. |
| `dipy_labelsbundles` | `LabelsBundlesFlow` | Extract original-space bundles from labels | Subject tractogram and `.npy` labels. |
| `dipy_median_otsu` | `MedianOtsuFlow` | Brain mask and optional masked image | 3D/4D image; b-values or `--vol_idx` for 4D masking. |
| `dipy_brain_mask` | `BrainMaskFlow` | Unified brain masking | `--method median_otsu`, `synthseg`, or `evac`; neural methods need optional backends. |
| `dipy_classify_tissue` | `ClassifyTissueFlow` | HMRF or DAM tissue classification | Image plus optional b-values/method-specific settings. |
| `dipy_buan_profiles` | `BundleAnalysisTractometryFlow` | Per-subject/group bundle profiles | Model bundle folder, subject folder, bundle/metric folders as needed. |
| `dipy_buan_shapes` | `BundleShapeAnalysis` | Bundle shape similarity matrices | Subject folder with group/recognized-bundle layout. |
| `dipy_buan_lmm` | `LinearMixedModelsFlow` | Linear mixed model analysis of BUAN profiles | HDF5 profile files and number of disks. |

Use `../../cli-workflows/` for parser mechanics and safe help probing; keep scientific parameter decisions here.
