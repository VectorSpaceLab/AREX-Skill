# Reconstruction Model Selection

Choose the smallest model that answers the scientific question and is supported by the acquisition. Do not pick a high-order ODF, deconvolution, MAPMRI, DSI, FORCE, or RUMBA workflow just because it is available.

## Quick Decision Table

| User intent | Prefer | Acquisition fit | Avoid when | Next route |
| --- | --- | --- | --- | --- |
| Fast tensor scalar maps: FA, MD, AD, RD, GA, RGB/color FA, eigenvalues/eigenvectors | DTI with `dipy.reconst.dti.TensorModel` or `dipy_fit_dti` | One or more b0 volumes plus enough non-collinear diffusion directions; appropriate for tiny smoke tests. | Crossing fibers, multi-compartment claims, or kurtosis interpretation are central. | Save maps through `../../io-data/`; tracking handoff may use tensor/PAM directions. |
| Robust tensor fit with outlier handling | `TensorModel(..., fit_method="RESTORE", sigma=...)` | DTI-style data with an estimated noise sigma. | Sigma is unknown or only a quick deterministic check is needed. | Preprocessing/noise estimation questions go to `../../denoising-preprocessing/`. |
| Kurtosis metrics: MK, AK, RK, DKI tensor | `dipy.reconst.dki.DiffusionKurtosisModel` or `dipy_fit_dki` | Multi-shell data with richer sampling than DTI; Dipy docs describe DKI-style acquisitions with at least two non-zero shells and enough directions. | Single-shell or low-gradient data; constrained/nonlinear methods without optional solver/runtime approval. | Save scalar maps through `../../io-data/`. |
| Free-water corrected tensor metrics | `dipy.reconst.fwdti.FreeWaterTensorModel` or `dipy_fit_fwdti` | Multi-shell free-water DTI acquisition; common examples compare against ordinary DTI. | Single-shell or low-gradient data. | Compare corrected metrics to baseline DTI as a sanity check. |
| Crossing-fiber fODFs and peaks with a response function | `dipy.reconst.csdeconv.ConstrainedSphericalDeconvModel`, MSMT-CSD, `dipy_fit_csd`, or `dipy_fit_msmtcsd` | Enough directions for the chosen SH order; response function supplied or estimated from plausible single-fiber tissue. MSMT may need WM/GM/CSF masks or a T1-derived tissue classification path. | Response is unreliable, gradients are sparse, tissue masks are unavailable for MSMT, or runtime is unapproved. | Peaks/PAM outputs go to `../../tracking-segmentation/`. |
| ODF peaks without response estimation | `CsaOdfModel`, `QballModel`, `OpdtModel`, `dipy_fit_csa`, `dipy_fit_qball`, or `dipy_fit_opdt` | Single-shell HARDI/QBI-style data with enough directions for `sh_order_max`. | Very low direction count, invalid signals, or a task only asking for tensor metrics. | Use `peaks_from_model`; validate peaks before tracking. |
| DSI or deconvolved DSI | `DiffusionSpectrumModel`, `DiffusionSpectrumDeconvModel`, `dipy_fit_dsi`, or `dipy_fit_dsid` | DSI-style Cartesian q-space acquisition. | Ordinary tensor, single-shell HARDI, or quick smoke tests. | Use explicit output directory and mark full runs `skip-expensive`. |
| GQI ODF/peaks | `GeneralizedQSamplingModel` or `dipy_fit_gqi` | Suitable diffusion sampling with at least one non-zero shell; choose method/sampling length intentionally. | User only needs scalar tensor maps. | Validate GFA/QA and peaks. |
| MAP-MRI scalar or propagator measures | `MapmriModel` or `dipy_fit_mapmri` | Multi-shell data with enough directions; requires `small_delta` and `big_delta` in the CLI. | Tiny smoke checks, low-gradient data, or unapproved expensive runs. | Record regularization/positivity settings and scalar outputs. |
| Sparse Fascicle Model peaks | `SparseFascicleModel` or `dipy_fit_sfm` | Response function and sphere assumptions are available; solver choice is understood. | Minimal data or absent response assumptions. | Validate peaks and solver behavior before tracking. |
| FORECAST deconvolution | `ForecastModel` or `dipy_fit_forecast` | Multi-shell data; examples use specialized acquisition assumptions. | General-purpose scalar mapping or low-gradient data. | Treat as specialized and validate acquisition first. |
| FORCE model | `FORCEModel` or `dipy_fit_force` | Method-specific diffusion acquisition; can cover broad b-value ranges in docs. | Routine DTI/DKI/CSD tasks or unapproved runtime. | Mark broad runs `skip-expensive`. |
| RUMBA-SD | `RumbaSDModel` Python API | HARDI/multi-shell/cartesian-capable model surface; iterative and potentially expensive. | Assuming an installed CLI named `dipy_fit_rumba`; no such command was verified in the installed CLI catalog. | Use API only unless CLI availability is re-verified. |
| IVIM, SDT, power map | `IvimModel`, CSD/SDT helpers, `dipy_fit_ivim`, `dipy_fit_sdt`, `dipy_fit_powermap` | Method-specific b-values or SH coefficient/power-map assumptions. | Ordinary tensor metrics or unsupported acquisition. | Document assumptions and run help first for CLI parameters. |

## Low-Gradient Case: DTI Versus CSD

When gradient count is low, choose DTI unless the user explicitly requires ODF peaks and the acquisition supports the requested SH order. CSD, CSA, QBall, OPDT, GQI, and SFM peak workflows can need enough DWI volumes to estimate spherical harmonic coefficients. A practical coefficient count is `(sh_order_max + 1) * (sh_order_max + 2) / 2`; the default `sh_order_max=8` needs 45 coefficients.

Recommended handling:

1. Check `data.shape[-1]`, `len(gtab.bvals)`, and the number of non-b0 volumes.
2. If the DWI count is below the SH requirement, use `TensorModel` for scalar maps or ask for a richer HARDI/multi-shell acquisition.
3. Lower `sh_order_max` only after documenting reduced angular detail and verifying enough directions remain.
4. If crossing-fiber peaks are still requested, report the acquisition risk and run a tiny masked subset before the full volume.
5. Do not pass all-zero or unsupported peaks to tracking; route only validated peak/PAM outputs to `../../tracking-segmentation/`.

## Response Function Choices

CSD, MSMT-CSD, SFM, and some deconvolution recipes are response-sensitive.

- Treat a supplied CSD response as `(evals, S0)` or workflow `frf` values only when eigenvalues are positive and prolate.
- Use automatic single-shell response estimation only when the mask/ROI contains plausible single-fiber white matter; validate the reported ratio/eigenvalues.
- For MSMT-CSD, expect WM/GM/CSF masks or T1-derived tissue classification; route mask creation and tissue segmentation questions to neighboring preprocessing/tracking skills.
- If response quality is uncertain, run DTI first to inspect FA and principal directions before fitting CSD.

## SH Order, Sphere, And Peaks

- Choose a Dipy sphere consistently, such as `dipy.data.default_sphere` or `dipy.data.get_sphere(name)`.
- Keep `sh_order_max` compatible with the number of diffusion volumes and with the requested angular detail.
- Start with `relative_peak_threshold=0.5`, `min_separation_angle=25`, `npeaks=5`, `normalize_peaks=True` for many ODF peak workflows.
- Use `return_sh=False` for faster smoke checks when SH coefficients are not needed.
- Preserve `legacy=True` unless interoperability requires a specific SH basis; record `sh_basis_type` and `legacy` when comparing to external tools.

## Skip Markers

Use these labels in plans and handoffs:

- `skip-network`: examples or data loaders would download datasets.
- `skip-expensive`: full-image MAPMRI, RUMBA, FORCE, CSD/MSMT-CSD, DSI/DSID, FORECAST, or large peak fitting is not required or not approved.
- `skip-optional`: visualization, deep-learning, GPU, optional solver, or GUI dependency is absent from a base install.
