---
name: denoising-preprocessing
description: "Choose and run Dipy denoising and preprocessing steps, including
  NLMeans, local PCA, MPPCA, Patch2Self, Gibbs removal, noise estimation, bias
  correction, and pre-fit validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Denoising And Preprocessing

Use this sub-skill when a Dipy task needs denoising or preprocessing before reconstruction, tracking, segmentation, or metric extraction: `NLMeans`, `localpca`, `mppca`, `Patch2Self`, Gibbs ringing removal, noise estimation, DWI bias-field correction, preprocessing masks, and validation of 3D/4D volume, mask, sigma, and patch-radius choices.

## Route First

- Use `../io-data/` for loading/saving NIfTI files, b-values/b-vectors, `GradientTable` construction from files, affine/header preservation, and image/gradient shape validation.
- Use `../reconstruction-models/` after preprocessing when the next task is tensor/CSD/DKI/ODF/peak fitting or reconstruction metric generation.
- Use `../tracking-segmentation/` for brain masks, tissue classification, streamline tracking, segmentation, and tractometry; keep only preprocessing-specific masks here.
- Use `../cli-workflows/` for console-entry discovery, parser behavior, `--help` probing, globbing semantics, and generic `dipy_*` command mechanics.
- Treat neural-network surfaces such as `dipy_evac_plus` and `dipy_correct_biasfield --method n4` as optional because base installs may lack model assets or ML dependencies.

## Core References

- `references/api-reference.md` lists denoising/preprocessing APIs, signatures, array contracts, and validation checks.
- `references/workflows.md` gives decision rules and safe API/CLI recipes for NLMeans, LPCA, MPPCA, Patch2Self, Gibbs removal, and bias correction.
- `references/troubleshooting.md` maps common shape, sigma, patch, mask, CLI, and optional-dependency failures to concrete fixes.
- `scripts/dipy_denoise_smoke.py` runs deterministic tiny in-memory checks and prints JSON; it does not download data or write persistent outputs.

## Fast Operating Pattern

1. Classify the preprocessing goal: suppress random noise, estimate noise, remove Gibbs ringing, correct smooth DWI intensity bias, or validate inputs before fitting.
2. Confirm data dimensionality before choosing an API: PCA and Patch2Self need 4D DWI data; NLMeans accepts 3D or 4D; Gibbs accepts 2D, 3D, or 4D.
3. Validate `data.shape[-1]` against b-values/b-vectors for gradient-aware paths and validate any mask with `mask.shape == data.shape[:3]`.
4. Choose the method from available information: use NLMeans with a credible `sigma`, LPCA with `sigma` or a `gtab`, MPPCA when noise is unknown and volume count supports local PCA, and Patch2Self for self-supervised DWI denoising with enough volumes.
5. Keep parameters conservative for first runs: small explicit output directories for CLIs, `num_processes=1` for deterministic Gibbs probes, and tiny synthetic arrays for smoke tests.
6. After preprocessing, validate finite values, preserved shape, expected dtype or requested `out_dtype`, nonempty in-mask output, and no accidental all-zero background expansion.

## Safety Defaults

- Prefer in-memory synthetic checks and existing user-provided images; do not fetch datasets, import visualization, train models, or download neural-network weights unless explicitly requested.
- Avoid running full-image Patch2Self, MPPCA, bias correction, or multi-process Gibbs on large data until the user confirms runtime expectations.
- If running inside a source checkout shadows the installed package and `import dipy` fails because generated version metadata is missing, run smoke checks from outside the checkout or use a normal installed package environment.
- Do not import `peaks_from_model` from `dipy.reconst.peaks`; route reconstruction to `../reconstruction-models/`, where the verified import is `dipy.direction.peaks.peaks_from_model`.
