# Reconstruction Workflows

These workflows are safe patterns for installed Dipy APIs and reconstruction console commands. They avoid downloads, visualization, training, and destructive writes.

## API Workflow: Tiny Tensor Fit

1. Create explicit `bvals` and unit `bvecs`; include at least one b0.
2. Build `gtab = gradient_table(bvals, bvecs=bvecs, b0_threshold=50, atol=0.01)`.
3. Simulate a positive signal with `dipy.sims.voxel.multi_tensor(..., snr=None)` or receive already-loaded data from `../../io-data/`.
4. Reshape data to `spatial_shape + (len(bvals),)` and create `mask.shape == spatial_shape`.
5. Fit `TensorModel(gtab, fit_method="OLS" or "WLS", min_signal=1e-6).fit(data, mask=mask)`.
6. Validate `fit.evals`, `fit.evecs`, FA range, metric shapes, and nonzero mask coverage.
7. Use `scripts/dipy_tensor_smoke.py --json` for a bundled deterministic smoke test.

## API Workflow: ODF Peaks From A Model

1. Confirm acquisition supports the model and `sh_order_max`; see `model-selection.md`.
2. Load or build `gtab`; route file parsing and bval/bvec validation to `../../io-data/`.
3. Build an ODF-capable model, such as `CsaOdfModel(gtab, sh_order_max=4, min_signal=1e-5)` for a small CSA workflow or `ConstrainedSphericalDeconvModel(gtab, response, sh_order_max=8)` for CSD.
4. Choose a sphere from `dipy.data`, such as `default_sphere` or `get_sphere(name)`.
5. Call `peaks_from_model(model, data, sphere, relative_peak_threshold=0.5, min_separation_angle=25, mask=mask, return_sh=True, sh_order_max=sh_order_max, normalize_peaks=True, parallel=False)`.
6. Validate `peak_directions.shape == data.shape[:-1] + (npeaks, 3)`, `gfa.shape == data.shape[:-1]`, and peak values are nonzero where expected.
7. Route downstream tractography to `../../tracking-segmentation/` with sphere, thresholds, SH basis, response, and mask assumptions recorded.

## API Workflow: Scalar Map Validation

After tensor, kurtosis, or free-water fitting:

- Replace NaNs before interpretation: `fa = np.nan_to_num(fractional_anisotropy(fit.evals))`.
- Clip/report FA in `[0, 1]`, matching Dipy workflow behavior.
- Check `np.isfinite(metric[mask]).all()` for FA, MD, AD, RD, MK, AK, RK, free-water fraction, or model-specific scalar maps.
- Treat all-zero maps inside a nonempty mask as a failure signal; re-check mask, signal clipping, b0 threshold, gradient table, and model choice.
- Use `../../io-data/` to save NIfTI outputs with the correct affine, dtype, and filename policy.

## Reconstruction CLI Commands

Installed reconstruction entry points are file-producing workflows backed by `dipy.workflows.reconst`. In the verified CLI catalog, `cli_flows` values are `(module, class-name)` tuples.

| Command | Backing flow | Main use | Notes |
| --- | --- | --- | --- |
| `dipy_fit_dti` | `ReconstDtiFlow` | Tensor fit and DTI scalar metrics. | Supports `fit_method`, `b0_threshold`, `npeaks`, `save_metrics`, tensor output style, PAM, and extracted peak maps. |
| `dipy_fit_dki` | `ReconstDkiFlow` | DKI metrics plus DTI-like maps. | Needs richer sampling than DTI; common outputs include MK/AK/RK and DKI tensor. |
| `dipy_fit_csd` | `ReconstCSDFlow` | Single-shell single-tissue CSD peaks/PAM. | Uses response estimation or `frf`; validates SH volume count. |
| `dipy_fit_msmtcsd` | `ReconstCSDFlow` with MSMT mode | Multi-shell multi-tissue CSD. | May need T1 or WM/GM/CSF masks; `iso` below 3 is rejected. |
| `dipy_fit_csa` | `ReconstQBallBaseFlow` | CSA ODF peaks. | Shares QBall base flow with method selection. |
| `dipy_fit_qball` | `ReconstQBallBaseFlow` | QBall ODF peaks. | Validate `sh_order_max` and DWI count. |
| `dipy_fit_opdt` | `ReconstQBallBaseFlow` | OPDT ODF peaks. | Validate SH order and signal clipping. |
| `dipy_fit_dsi` | `ReconstDsiFlow` | DSI ODF/peaks. | DSI-style Cartesian q-space only. |
| `dipy_fit_dsid` | `ReconstDsiFlow` | Deconvolved DSI. | CLI dispatch sets deconvolution mode for this command. |
| `dipy_fit_gqi` | `ReconstGQIFlow` | GQI ODF/peaks. | Choose method/sampling length intentionally. |
| `dipy_fit_mapmri` | `ReconstMAPMRIFlow` | MAP-MRI scalar/peak outputs. | Requires `small_delta` and `big_delta`; mark broad runs `skip-expensive`. |
| `dipy_fit_sfm` | `ReconstSFMFlow` | Sparse Fascicle Model peaks. | Response and solver assumptions matter. |
| `dipy_fit_forecast` | `ReconstForecastFlow` | FORECAST deconvolution. | Specialized multi-shell workflow. |
| `dipy_fit_fwdti` | `ReconstFwdtiFlow` | Free-water tensor metrics. | Multi-shell free-water DTI. |
| `dipy_fit_force` | `ReconstForceFlow` | FORCE microstructure workflow. | Specialized and potentially expensive. |
| `dipy_fit_ivim` | `ReconstIvimFlow` | IVIM metrics. | Needs low-b and diffusion b-values appropriate for IVIM. |
| `dipy_fit_sdt` | `ReconstSDTFlow` | Spherical deconvolution transform. | Response/ratio-sensitive. |
| `dipy_fit_powermap` | `ReconstPowermapFlow` | Anisotropic power map. | Often supports tissue classification or CSD context. |

No installed `dipy_fit_rumba` command was verified. Use `RumbaSDModel` through Python APIs unless the command is rechecked in the active environment.

## CLI Safety Pattern

Run help before production commands:

```bash
dipy_fit_dti --help
```

Use explicit output directories and metrics:

```bash
dipy_fit_dti dwi.nii.gz bvals bvecs mask.nii.gz --out_dir recon_out --save_metrics fa md rgb eval evec
```

Before running any CLI:

1. Confirm input files exist and route file-format validation to `../../io-data/`.
2. Confirm `len(bvals) == data.shape[-1]` and mask shape matches the image spatial shape.
3. Use a fresh output directory or explicit output names to avoid overwriting previous results.
4. Mark full-image CSD/MSMT-CSD, MAPMRI, DSI/DSID, GQI, SFM, FORECAST, FORCE, and RUMBA work `skip-expensive` unless the user approves.
5. For optional visualization or neural-network paths, use `skip-optional`; a base install may lack `fury`, `matplotlib`, `torch`, or `tensorflow`.

## Common Outputs And Handoff

Tensor outputs can include `fa.nii.gz`, `ga.nii.gz`, `rgb.nii.gz`, `md.nii.gz`, `ad.nii.gz`, `rd.nii.gz`, `mode.nii.gz`, `evals.nii.gz`, `evecs.nii.gz`, `tensors.nii.gz`, `s0.nii.gz`, and `peaks.pam5`.

DKI outputs can include `mk.nii.gz`, `ak.nii.gz`, `rk.nii.gz`, `dti_tensors.nii.gz`, `dki_tensors.nii.gz`, DTI-like metrics, and `peaks.pam5`.

Peak/ODF workflows can include `peaks.pam5`, `shm.nii.gz`, `peaks_dirs.nii.gz`, `peaks_values.nii.gz`, `peaks_indices.nii.gz`, `gfa.nii.gz`, `sphere.txt`, `B.nii.gz`, and `qa.nii.gz`.

When handing off to another sub-skill, include:

- Model family, fit method, SH order, response, sphere, thresholds, normalization, and mask.
- Data assumptions: b0 threshold, b-vector tolerance, signal clipping, preprocessing, and acquisition limitations.
- Validation results: metric ranges, finite checks, nonzero in-mask coverage, shape checks, and skip markers.
