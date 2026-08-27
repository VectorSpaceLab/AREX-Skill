---
name: reconstruction-models
description: "Choose and fit Dipy diffusion reconstruction models, compute
  scalar maps, ODFs, peaks, tiny simulations, and reconstruction CLI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Reconstruction Models

Use this sub-skill when a task involves Dipy diffusion reconstruction: `TensorModel`, DKI, CSD/MSMT-CSD, CSA/QBall/OPDT, DSI/DSID, GQI, MAPMRI, SFM, FORECAST, FWDTI, FORCE, RUMBA, SH models, `peaks_from_model`, scalar maps, ODFs, simulated signals, or `dipy_fit_*` reconstruction commands.

## Route First

- Use `../io-data/` for loading/saving NIfTI images, b-values/b-vectors, `GradientTable` file ingestion, PAM files, tractograms, and image/gradient shape validation.
- Use `../denoising-preprocessing/` before fitting when the signal needs denoising, Gibbs removal, masking, noise estimation, bias correction, or invalid-signal repair.
- Use `../tracking-segmentation/` when reconstruction outputs become tracking inputs: peaks, PAM files, tensor directions, stopping criteria, tissue masks, segmentation, or tractometry.
- Use `../cli-workflows/` for console-entry discovery, parser behavior, help probing, batch globbing semantics, and translating API recipes into installed `dipy_*` commands.

## Core References

- `references/model-selection.md` explains how to choose DTI, DKI, CSD, CSA/QBall, DSI, GQI, MAPMRI, SFM, FWDTI, FORECAST, FORCE, RUMBA, IVIM, SDT, and power-map workflows.
- `references/api-reference.md` lists high-value Python APIs, signatures, shapes, outputs, and validation checks.
- `references/workflows.md` gives safe API and CLI recipes, output naming, handoff notes, and skip markers.
- `references/troubleshooting.md` maps reconstruction symptoms to causes, fixes, and validation checks.
- `scripts/dipy_tensor_smoke.py` runs a deterministic tiny synthetic `TensorModel` fit and emits JSON with finite FA/eigenvalue validation.

## Fast Operating Pattern

1. Confirm the reconstruction question and acquisition class before choosing a model; prefer the simplest scientifically adequate model.
2. Ensure diffusion volumes are on the last axis and `len(gtab.bvals) == data.shape[-1]`; masks must be exactly `data.shape[:-1]`.
3. Guard signals before fitting: finite numeric data, positive values for log-sensitive models, appropriate `b0_threshold`, and a mask that excludes background.
4. Fit with a mask when possible, compute model-specific maps or peaks, then validate finite values, expected shapes, and nonzero in-mask coverage.
5. For ODF/peak workflows, record sphere, `sh_order_max`, response function, thresholds, SH basis settings, and whether `parallel` was used.
6. For CLI workflows, run help first, set an explicit output directory, and treat full-image CSD/MSMT-CSD/MAPMRI/DSI/FORCE/RUMBA runs as `skip-expensive` unless authorized.

## Safety Defaults

- Prefer tiny synthetic arrays and `snr=None` simulations for smoke checks; avoid downloads, GUI rendering, neural-network surfaces, and benchmark-scale data by default.
- Do not claim `dipy_fit_rumba` is installed; use RUMBA as a Python API/specialized workflow surface unless an installed command is verified in the active environment.
- Use `dipy.direction.peaks.peaks_from_model`; do not import peaks from `dipy.reconst.peaks` for this Dipy version.
