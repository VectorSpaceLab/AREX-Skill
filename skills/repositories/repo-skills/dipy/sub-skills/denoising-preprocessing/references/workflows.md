# Denoising And Preprocessing Workflows

These workflows are safe patterns for Dipy denoising and preprocessing APIs and console commands. They avoid downloads, plotting, neural-network weight fetching, and destructive writes by default.

## Method Selection

| Situation | Prefer | Why | Validate |
| --- | --- | --- | --- |
| 3D structural-like or single-volume image with a sigma estimate | `nlmeans` | Works on 3D arrays and can use Rician or Gaussian noise assumptions. | Output shape/dtype equals input; residual is not all zero; mask is 3D if supplied. |
| 4D DWI with a reliable scalar or 3D sigma map | `localpca` | Uses diffusion-volume redundancy and a supplied noise estimate. | `data.ndim == 4`; patch fits spatial dimensions; mask and sigma map are spatial. |
| 4D DWI with unknown noise and enough volumes | `mppca` | Estimates sigma from local PCA via Marcenko-Pastur distribution. | Local sample count is suitable; `return_sigma=True` gives a finite 3D map. |
| 4D DWI where self-supervised denoising is acceptable | `patch2self` | Learns leave-one-volume-out predictions from the DWI itself. | `len(bvals) == data.shape[-1]`; enough volumes; v3 patch radius stays zero. |
| Visible edge-adjacent ringing before fitting | `gibbs_removal` | Removes Gibbs oscillations on 2D slices across 3D/4D data. | `slice_axis` is acquisition slice axis; shape preserved; use `inplace=False` when probing. |
| Smooth multiplicative intensity shading in DWI | `bias_field_correction` with `poly`, `bspline`, or `auto` | Estimates bias from mean b0 and applies it to all volumes. | b0 volumes exist; mask is nonempty; bias field is finite and spatially smooth. |

## API Workflow: Preflight Validation

1. Load image, affine, bvals, bvecs, and masks through `../../io-data/` when starting from files.
2. Validate finite numeric arrays and rank: `data.ndim == 4` for DWI methods; `arr.ndim in (3, 4)` for NLMeans; `vol.ndim in (2, 3, 4)` for Gibbs.
3. Validate gradients for DWI methods: `len(bvals) == data.shape[-1]`; `bvecs.shape == (len(bvals), 3)`; b0 threshold matches acquisition.
4. Validate masks: 3D, same spatial shape as data, nonempty, and not accidentally all-background.
5. Validate patch geometry: `2 * patch_radius + 1` fits each non-singleton spatial axis; patch radius is scalar or length 3.
6. Record skip markers before expensive or optional paths: `skip-expensive` for full image Patch2Self/MPPCA/bias correction; `skip-optional` for NN or plotting surfaces.

## API Workflow: NLMeans

1. Choose or estimate `sigma`; for 4D, use scalar, length-`N` vector, or 3D map.
2. Pick noise model: `rician=True` for magnitude MRI, `False` for Gaussian synthetic or already-complex-derived data.
3. Choose method: start with `method='blockwise'`; use `classic` only when reproducing older behavior or comparing methods.
4. Run a small ROI or temporary copy first for large data; set `num_threads=1` for deterministic smoke checks.
5. Validate output shape, dtype, finite values, mask zeroing outside ROI, and plausible residual magnitude.

```python
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.nlmeans import nlmeans

sigma = estimate_sigma(arr, N=0)
denoised = nlmeans(arr, sigma=sigma, mask=mask, method="blockwise", rician=True, num_threads=1)
```

## API Workflow: LPCA And MPPCA

1. Use LPCA when a sigma estimate is supplied or when a `GradientTable` is available for internal PCA noise estimation.
2. Use MPPCA when sigma is unknown and the volume count/spatial patch size is scientifically appropriate.
3. Start with `patch_radius=1` on small data; increase only when spatial dimensions and volume count justify it.
4. Use `pca_method='eig'` for speed; use `svd` for comparison or suspected numerical issues.
5. Validate that warnings about insufficient local samples are understood; do not hide them with `suppress_warning=True` unless the user accepts the limitation.
6. If `return_sigma=True`, validate `sigma_map.shape == data.shape[:3]` and finite in-mask values.

```python
from dipy.denoise.localpca import localpca, mppca

lpca_data = localpca(data, sigma=sigma, mask=mask, patch_radius=1, pca_method="eig")
mppca_data, sigma_map = mppca(data, mask=mask, patch_radius=1, return_sigma=True)
```

## API Workflow: Patch2Self

1. Confirm `data.ndim == 4` and `len(bvals) == data.shape[-1]` before calling.
2. Prefer `version=3` with default `patch_radius=(0, 0, 0)` unless reproducing v1 behavior.
3. Choose `model='ols'` for default behavior, `ridge` with `alpha` for stronger regularization, and `lasso` only when scikit-learn support and runtime are acceptable.
4. Use `b0_denoising=False` if b0 volumes must pass through unchanged; verify with `bvals <= b0_threshold`.
5. For v3, pass an existing `tmp_dir` only when explicitly managing temporary storage; do not point at non-existent directories.
6. Validate output shape, finite values, and whether `clip_negative_vals` or `shift_intensity` changed intensity interpretation.

```python
from dipy.denoise.patch2self import patch2self

denoised = patch2self(data, bvals, model="ols", version=3, patch_radius=(0, 0, 0), verbose=False)
```

## API Workflow: Gibbs Ringing Removal

1. Identify the acquisition slice axis, usually one of `0`, `1`, or `2`.
2. Use `inplace=False` for validation or if the original array is needed later.
3. Use `num_processes=1` for deterministic tiny checks; use higher values only for larger production data.
4. Validate shape preservation and finite output; inspect or summarize residual near sharp edges if evaluating effect.

```python
from dipy.denoise.gibbs import gibbs_removal

unring = gibbs_removal(vol, slice_axis=2, n_points=3, inplace=False, num_processes=1)
```

## API Workflow: DWI Bias Correction

1. Build or receive a `GradientTable` and confirm at least one b0 volume.
2. Provide a mask when possible; otherwise the API computes one from the mean b0 using median Otsu.
3. Choose `method='poly'` for smooth global bias and fast cohort-scale correction; choose `bspline` for more flexible smooth fields; choose `auto` when unsure and runtime is acceptable.
4. For small probes, reduce `pyramid_levels` and `n_iter`; for production, use defaults or documented study parameters.
5. Use `return_bias_field=True` when QA needs the multiplicative field; use `zero_background=True` if saved bias background should be `1.0`.
6. Validate corrected data shape/dtype, finite positive bias values in mask, and that background outside mask is zeroed in corrected data.

```python
from dipy.denoise.bias_correction import bias_field_correction

corrected, bias = bias_field_correction(
    data, gtab, mask=mask, method="poly", pyramid_levels=(2, 1),
    n_iter=1, robust=False, gradient_weighting=False, return_bias_field=True,
)
```

## CLI Commands

Installed denoising and preprocessing entry points are file-producing workflows backed by `dipy.workflows.denoise` or `dipy.workflows.nn`. Run help first and use a fresh output directory.

| Command | Backing flow | Main inputs | Default output | Notes |
| --- | --- | --- | --- | --- |
| `dipy_denoise_nlmeans` | `NLMeansFlow` | input image; optional `--sigma`, `--patch_radius`, `--block_radius`, `--rician`, `--method` | `dwi_nlmeans.nii.gz` | If `sigma` is zero, workflow estimates sigma with `estimate_sigma`. |
| `dipy_denoise_lpca` | `LPCAFlow` | DWI, bvals, bvecs | `dwi_lpca.nii.gz` | If `--sigma 0`, workflow estimates sigma with `pca_noise_estimate`. |
| `dipy_denoise_mppca` | `MPPCAFlow` | DWI | `dwi_mppca.nii.gz`; optional `dwi_sigma.nii.gz` | `--return_sigma` saves the sigma map. |
| `dipy_denoise_patch2self` | `Patch2SelfFlow` | DWI and bvals | `dwi_patch2self.nii.gz` | `--ver 3` is default in the workflow; v3 rejects nonzero patch radius at the API level. |
| `dipy_gibbs_ringing` | `GibbsRingingFlow` | input image | `dwi_unring.nii.gz` | `--slice_axis`, `--n_points`, and `--num_processes` control unringing. |
| `dipy_correct_biasfield` | `BiasFieldCorrectionFlow` | image; DWI methods require `--bval` and `--bvec`; optional mask | `dwi_biasfield_corrected.nii.gz` or `t1_biasfield_corrected.nii.gz`; `bias_field.nii.gz` for DWI methods | `--method n4` is optional NN/weight-dependent; `poly`, `bspline`, and `auto` are DWI-oriented. |
| `dipy_evac_plus` | `EVACPlusFlow` | input image | `brain_mask.nii.gz` and optional `brain_masked.nii.gz` | Optional neural-network brain extraction; route general masks to `../../tracking-segmentation/`. |

### CLI Safety Pattern

```bash
dipy_denoise_mppca --help
dipy_denoise_mppca dwi.nii.gz --patch_radius 2 --return_sigma --out_dir denoise_mppca_out
```

Before running a CLI:

1. Validate file paths and image/gradient shapes through `../../io-data/`.
2. Run `command --help` in the active environment to confirm option spelling.
3. Use explicit `--out_dir` and avoid existing output names unless overwrite behavior is intentional.
4. Treat large Patch2Self/MPPCA/NLMeans runs as potentially expensive; estimate runtime on a crop or representative subset first.
5. Mark NN commands and `dipy_correct_biasfield --method n4` as optional unless dependencies and model assets are verified.

## Handoff After Preprocessing

When handing off to reconstruction or tracking, include:

- Method and parameters: sigma source, patch radius, PCA method, Patch2Self version/model, Gibbs slice axis, bias method, mask source, and b0 threshold.
- Validation: input/output shapes, finite checks, dtype, mask coverage, residual or QA summary, and skip markers for expensive/optional work.
- File metadata: affine/header preservation and output paths are owned by `../../io-data/` but should be recorded in the handoff.
