# Registration And Alignment Troubleshooting

Use this matrix to debug Dipy reslice, registration, motion correction, SLR, and BundleWarp tasks. Route file-format, gradient, NIfTI header, and tractogram reference problems to `../../io-data/` when they are the root cause.

| Symptom | Likely cause | Recovery action | Validation check |
| --- | --- | --- | --- |
| `reslice` raises that data dimension should be 3 or 4 | Input array has unsupported dimensionality, often an accidental extra singleton axis | Squeeze or select the intended 3D/4D image before reslicing; keep metadata with the corrected array | `data.ndim in (3, 4)` and output shape changes only in the first three axes. |
| `reslice` raises about `num_processes=0` | Worker count zero is invalid | Use `1` for deterministic single-process probes or `-1` for automatic worker count | Script completes and 4D last dimension is preserved. |
| `reslice` raises invalid interpolation order | `order` is outside `0..5` or an unsupported string | Use integer `0..5`, `"lanczos"`, `"lanczos2"`, or `"lanczos3"`; use `order=0` for labels | Output dtype/values are plausible and labels are not blended. |
| `reslice` raises invalid mode, especially `mirror` with Lanczos | Lanczos supports a smaller mode set than scipy spline interpolation | For Lanczos use `constant`, `nearest`, `reflect`, or `wrap`; for spline interpolation `mirror` is also available | Tiny smoke reslice passes with the chosen mode. |
| Resliced output is unexpectedly huge | Target voxel size is much smaller than input zooms or `new_shape` was mis-specified | Recompute `zooms / new_zooms * shape`, crop for tests, or choose coarser target voxel sizes | Estimated voxel count and memory fit available resources. |
| Resliced labels contain fractional values | Labels/masks were interpolated with linear/spline order | Re-run with `order=0` and suitable boundary mode | Unique labels remain integer-like and expected label set is preserved. |
| Affine registration says affines are required | Arrays were passed without `moving_affine` and `static_affine` | Provide both affines, or pass NIfTI images/paths that carry affines | Registration starts and output shape equals static shape. |
| Affine registration raises invalid pipeline element | Pipeline contains unsupported transform names | Use only `center_of_mass`, `translation`, `rigid`, `rigid_isoscaling`, `rigid_scaling`, or `affine` | Pipeline sanitization succeeds and final matrix is `(4, 4)`. |
| Requesting metric from center-of-mass fails | Center of mass has no optimizer metric | Do not set `ret_metric=True` for `pipeline=["center_of_mass"]`; use a later transform if quality metric is needed | Function returns moved data and matrix without metric. |
| Output is in the wrong space | Static and moving roles were swapped, or an old static grid was reused for apply-transform | Treat static as reference/domain and moving as source/codomain; re-run with correct order | Output shape and affine match the intended static/reference image. |
| Affine registration is slow or stalls | Full-resolution data, default iterations, dense sampling, or background-heavy images | Test on a crop; lower `level_iters` for probes; use masks; consider sparse `sampling_proportion` | Small probe improves overlap and runtime estimate is acceptable. |
| Affine result is implausible or sheared too much | Transform model has too many degrees of freedom for the data | Start with `rigid` or `rigid_scaling`; add affine only if needed and validated | Determinant, scale terms, and visual/numeric overlap are plausible. |
| SyN raises invalid metric | CLI/API metric name is not one of the supported choices | Use `CC`, `SSD`, or `EM` in Python; CLI accepts lowercase `cc`, `ssd`, or `em` | Optimizer builds the expected metric object. |
| SyN fails on dimension mismatch | Static and moving have different dimensionality or unsupported 4D inputs | Select 2D slices or 3D volumes; average/select 4D volumes before SyN | `static.ndim == moving.ndim` and each is 2D or 3D. |
| SyN produces extreme or anatomically implausible warps | Missing affine prealignment, too many iterations, bad metric for modality pair, or poor masks | Run affine first and pass `prealign`; reduce iterations; choose metric for modality; mask irrelevant background | Displacement field is finite, smooth, and improves landmarks without folding-like artifacts. |
| `dipy_apply_transform` rejects transform type | Transform type is not exactly affine or diffeomorphic | Use `--transform_type affine` for `.txt` matrices or `--transform_type diffeomorphic` for displacement NIfTI | Output file is written with static grid shape. |
| Applying transform to labels blurs classes | Linear interpolation was used for labels/masks | Use `--interpolation nearest` or mapping transform with nearest interpolation | Class values remain discrete. |
| Diffeomorphic transform application fails or gives nonsense | Displacement field is not in Dipy mapping shape `(X, Y, Z, 3, 2)` or domain/codomain images do not match estimation | Use Dipy `write_mapping`/`dipy_align_syn` outputs; keep original static and moving reference images with the transform | Field shape and reference images match the registration run. |
| Motion correction warns b0 threshold is too low | `b0_threshold` is below the lowest b0-like value | Increase threshold or inspect b-values in `../../io-data/` | `gtab.b0s_mask` contains the intended reference volumes. |
| Motion correction fails building `GradientTable` | b-values/b-vectors do not match DWI volume count or b-vectors are not unit length within tolerance | Route gradient file validation to `../../io-data/`; fix transposed bvecs or set appropriate `bvecs_tol` only if justified | Number of gradients equals `data.shape[-1]` and non-b0 bvec norms are near 1. |
| Motion correction is too expensive | Full DWI series and default affine iterations are costly | Run on a cropped subset or fewer volumes first; reduce `level_iters` for a runtime probe | Corrected image shape equals input and affine stack has one matrix per volume. |
| SLR returns poor alignment | Bundles are in different coordinate spaces, not comparable anatomy, or insufficient streamlines after filtering | Confirm coordinate units/reference via `../../io-data/`; reduce `greater_than`/increase `less_than`; try rigid before affine | Moved streamlines overlap static better and matrix is finite. |
| `dipy_slr` logs empty static or moving file | Tractogram is empty or filters removed all streamlines | Check input loading, length filters, and clustering thresholds; route upstream segmentation to `../../tracking-segmentation/` | Nonzero streamline counts before SLR. |
| SLR save fails due to invalid bbox | Streamlines fall outside tractogram bounding box after transform | Confirm reference image, space, and origin; use `remove_invalid_streamlines` only when scientifically acceptable | Saved tractogram passes bbox validation or invalid streamlines are explicitly removed. |
| BundleWarp warns about `alpha<=0.01` | Deformation setting can radically alter anatomy | Start with `alpha=0.3` or `0.5`; reserve very low alpha for explicit high-deformation experiments | Displacement magnitudes and bundle shape remain plausible. |
| BundleWarp fails importing pandas-dependent outputs | BundleWarp creates warp metadata as a pandas DataFrame and pandas may be unavailable in some environments | Check whether pandas is installed before promising BundleWarp; fall back to SLR when nonlinear warp metadata cannot be produced | Import succeeds and warp arrays are saved, or task is scoped to SLR. |
| Overlay/QA plotting fails | `matplotlib`, FURY, or display backend is unavailable | Use numeric QA first; install optional visualization dependencies only if the user requests figures | Core registration APIs still run without plotting. |

## Quick Isolation Sequence

1. Run `scripts/dipy_reslice_smoke.py` to confirm Dipy imports and core reslice behavior.
2. Validate input shapes and affines before registration; arrays need explicit affines.
3. Run a crop/small-volume affine registration before SyN or motion correction.
4. Save transforms separately and apply them to one small target image before batch processing.
5. For streamline tasks, verify nonempty streamline counts, coordinate space, and length filters before SLR or BundleWarp.

## When To Stop And Re-scope

- If registration quality cannot be validated numerically or visually, report uncertainty instead of increasing deformation strength.
- If the task is mainly about tractogram file validity, gradient tables, or NIfTI metadata, route to `../../io-data/`.
- If the task is mainly about recognizing, segmenting, or evaluating bundles after alignment, route to `../../tracking-segmentation/`.
- If optional plotting or neural-network dependencies are missing, keep the registration workflow functional and document visualization as optional.
