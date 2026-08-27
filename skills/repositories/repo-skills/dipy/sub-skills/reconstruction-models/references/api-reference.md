# Reconstruction API Reference

This reference covers Dipy reconstruction surfaces future agents can use without opening the source checkout. File parsing, NIfTI/tractogram/PAM IO, and bval/bvec repair are routed to `../../io-data/`.

## Gradient Tables And Synthetic Signals

| API | Use | Key contract | Validate |
| --- | --- | --- | --- |
| `dipy.core.gradients.gradient_table(bvals, *, bvecs=None, big_delta=None, small_delta=None, b0_threshold=50, atol=0.01, btens=None)` | Build model-ready diffusion gradient metadata from arrays. | `bvals` length is `N`; `bvecs` is `(N, 3)` or `(3, N)`; b-values `<= b0_threshold` are b0; non-b0 b-vectors should be unit length within `atol`. | `len(gtab.bvals) == data.shape[-1]`; expected `gtab.b0s_mask.sum()`; non-b0 vector norms are near 1. |
| `dipy.core.gradients.GradientTable(gradients, *, big_delta=None, small_delta=None, b0_threshold=50, btens=None)` | Lower-level gradient table constructor when gradients are already assembled. | Prefer `gradient_table` for ordinary array/file-derived bvals/bvecs. | Same length and b0 checks as above. |
| `dipy.sims.voxel.multi_tensor(gtab, mevals, *, S0=1.0, angles=((0, 0), (90, 0)), fractions=(50, 50), snr=20, rng=None)` | Simulate deterministic tiny diffusion signals for smoke checks. | `mevals` is `(K, 3)`; `fractions` must sum to 100; use `snr=None` for noise-free deterministic output. | Returned signal is length `N`, finite, and positive before fitting. |

## Tensor APIs

| API | Use | Key options | Typical outputs |
| --- | --- | --- | --- |
| `dipy.reconst.dti.TensorModel(gtab, *args, fit_method='WLS', return_S0_hat=False, **kwargs)` | DTI tensor fitting and scalar metrics. | `fit_method`: `WLS`, `LS`/`OLS`, `NLLS`, `RT`/`restore`/`RESTORE`; `min_signal` must be positive when supplied; `return_S0_hat=True` exposes S0 for supported methods. | `fit.evals`, `fit.evecs`, `fit.quadratic_form`, `fit.fa`, `fit.md`, `fit.ad`, `fit.rd`, `fit.color_fa`, optional `fit.S0_hat`. |
| `dipy.reconst.dti.fractional_anisotropy(evals, *, axis=-1)` | Compute FA from eigenvalues. | Use `np.nan_to_num` and clip/report `[0, 1]` as Dipy workflows do. | Scalar spatial array. |
| `dipy.reconst.dti.mean_diffusivity`, `axial_diffusivity`, `radial_diffusivity`, `geodesic_anisotropy`, `mode`, `color_fa` | Compute common tensor metrics. | Pass eigenvalues/eigenvectors or tensor forms matching the helper. | Metric maps with spatial shape; RGB has final axis `3`. |

`TensorModel.fit(data, mask=mask)` expects diffusion volumes on the last axis. If supplied, `mask.shape` must equal `data.shape[:-1]`.

## Kurtosis And Free-Water APIs

| API | Use | Key options | Validate |
| --- | --- | --- | --- |
| `dipy.reconst.dki.DiffusionKurtosisModel(gtab, *args, fit_method='WLS', return_S0_hat=False, **kwargs)` | DKI fitting for tensor-like metrics plus kurtosis maps. | Common safe methods are `WLS` and `OLS`; constrained/nonlinear methods may require optional solver/runtime choices; `min_signal` must be positive. | Multi-shell data; finite `fit.model_params`, `fit.evals`, `fit.fa`, `fit.mk()`, `fit.ak()`, and `fit.rk()` inside the mask. |
| `dipy.reconst.fwdti.FreeWaterTensorModel(gtab, fit_method='NLS', ...)` | Free-water corrected tensor metrics and free-water fraction. | Use only for suitable multi-shell data; compare to baseline DTI. | Corrected metrics and free-water fraction finite and plausible inside mask. |
| `dipy.reconst.msdki.MeanDiffusionKurtosisModel(gtab, ...)` | Mean-signal DKI variants. | Multi-shell acquisition; not a replacement for low-gradient DTI. | Mean-signal metrics finite and not all zero in mask. |

## ODF, SH, And Peak APIs

| API | Use | Key options | Validate |
| --- | --- | --- | --- |
| `dipy.reconst.csdeconv.ConstrainedSphericalDeconvModel(gtab, response, *, reg_sphere=None, sh_order_max=8, lambda_=1, tau=0.1, convergence=50)` | Single-shell single-tissue CSD fODF model. | `response` is commonly `(evals, S0)`; estimate or pass a known response; choose `sh_order_max` from acquisition. | Positive/prolate response; enough volumes for SH order; nonzero peaks/GFA where expected. |
| `dipy.reconst.mcsd.MultiShellDeconvModel` | Multi-shell multi-tissue CSD. | Requires multi-shell response and tissue compartment setup; CLI wrapper can classify tissues from T1 or power map. | WM/GM/CSF mask shapes match DWI spatial shape; `iso >= 3` for CLI MSMT path. |
| `dipy.reconst.shm.CsaOdfModel(gtab, sh_order_max, *, smooth=0.006, min_signal=1e-05, assume_normed=False)` | CSA ODF model. | Keep `min_signal > 0`; use `assume_normed=True` only when data is already normalized. | Enough directions; finite ODF/GFA; not all-zero peaks. |
| `dipy.reconst.shm.QballModel`, `dipy.reconst.shm.OpdtModel` | QBall/OPDT ODF models. | Similar SH-order and signal requirements to CSA. | Validate peak arrays and GFA. |
| `dipy.direction.peaks.peaks_from_model(model, data, sphere, relative_peak_threshold, min_separation_angle, *, mask=None, return_odf=False, return_sh=True, gfa_thr=0, normalize_peaks=False, sh_order_max=8, sh_basis_type=None, legacy=True, npeaks=5, B=None, invB=None, parallel=False, num_processes=None)` | Fit an ODF-capable model voxelwise and return `PeaksAndMetrics`. | Import from `dipy.direction.peaks`; set `return_sh=False` for faster smoke checks; use `parallel=False` for tiny deterministic checks. | `peak_directions.shape == data.shape[:-1] + (npeaks, 3)`; `gfa.shape == data.shape[:-1]`; mask shape matches. |

`peaks_from_model` is verified from `dipy.direction.peaks`. Do not use `dipy.reconst.peaks` for this package version.

## Specialized Model Inventory

| Family | Representative APIs | Use |
| --- | --- | --- |
| DSI/DSID | `dipy.reconst.dsi.DiffusionSpectrumModel`, `DiffusionSpectrumDeconvModel` | Cartesian q-space ODF/peaks and deconvolution. |
| GQI | `dipy.reconst.gqi.GeneralizedQSamplingModel` | Generalized q-sampling ODF/peaks; method and sampling length matter. |
| MAPMRI | `dipy.reconst.mapmri.MapmriModel` | MAP-MRI propagator and scalar measures such as RTOP, MSD, QIV, RTAP/RTPP, and non-Gaussianity. |
| SFM | `dipy.reconst.sfm.SparseFascicleModel` | Sparse fascicle peaks using response/sphere/solver assumptions. |
| FORECAST | `dipy.reconst.forecast.ForecastModel` | Multi-shell spherical deconvolution. |
| FORCE | `dipy.reconst.force.FORCEModel` | Specialized microstructure reconstruction; validate import and acquisition. |
| RUMBA | `dipy.reconst.rumba.RumbaSDModel` | Iterative spherical deconvolution; potentially expensive. |
| IVIM | `dipy.reconst.ivim.IvimModel` | IVIM metrics from low-b and diffusion data. |
| SHORE/MAP/Q-space variants | `dipy.reconst.shore.ShoreModel`, `qti`, `qtdmri`, `cti`, `dki_micro` modules | Advanced/research-specific workflows; validate acquisition and runtime before use. |

## Minimal Tensor Pattern

```python
import numpy as np
from dipy.core.gradients import gradient_table
from dipy.reconst.dti import TensorModel, fractional_anisotropy

bvals = np.array([0, 1000, 1000, 1000, 1000, 1000, 1000.0])
bvecs = np.array([
    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
    [0.7071, 0.7071, 0], [0.7071, 0, 0.7071], [0, 0.7071, 0.7071],
])
gtab = gradient_table(bvals, bvecs=bvecs)
data = np.ones((1, 1, 1, len(bvals)), dtype=float)
mask = np.ones((1, 1, 1), dtype=bool)
fit = TensorModel(gtab, fit_method="OLS", min_signal=1e-6).fit(data, mask=mask)
fa = np.nan_to_num(fractional_anisotropy(fit.evals))
```

Use `scripts/dipy_tensor_smoke.py --json` for a stronger deterministic synthetic check that validates finite FA and eigenvalues.
