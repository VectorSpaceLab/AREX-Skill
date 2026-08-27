---
name: maskers-regions
description: "Choose and use Nilearn maskers, atlas region extraction, inverse
  transforms, and masker reports for samples-by-features neuroimaging
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Maskers and Regions

Use this sub-skill when a Nilearn task needs a scikit-learn-style masker or
region API to turn 3D/4D images into arrays shaped as samples by features,
region time series, or reconstructed images from extracted signals.

## Read First

- Pick a class from [API Reference](references/api-reference.md) before writing
  code; labels, maps, spheres, whole-brain voxels, and multi-subject inputs
  have different contracts.
- Follow [Workflows](references/workflows.md) for fit/transform,
  inverse-transform, atlas extraction, multi-run confounds, and report recipes.
- Use [Troubleshooting](references/troubleshooting.md) for empty masks, lost
  labels, overlaps, confound length errors, resampling surprises, and optional
  plotting/report failures.
- Run `python scripts/smoke_maskers_regions.py --help` for the bundled
  no-network synthetic smoke check.

## Route Here

- Choose `NiftiMasker` or `MultiNiftiMasker` for voxelwise whole-brain or
  mask-restricted matrices.
- Choose `NiftiLabelsMasker`, `NiftiMapsMasker`, or `NiftiSpheresMasker` for
  atlas labels, probabilistic maps, or coordinate seeds.
- Use multi-NIfTI labels/maps maskers when each subject/run should return its
  own array and `confounds`/`sample_mask` are per-image lists.
- Use `RegionExtractor`, `connected_regions`, `connected_label_regions`,
  `Parcellations`, and `ReNA` for deriving or splitting regions before signal
  extraction.
- Generate masker HTML reports with `generate_report()` after fitting or
  transforming, while keeping plotting optional dependency issues separate.

## Route Elsewhere

- Use [data-io-signal](../data-io-signal/SKILL.md) for raw `apply_mask`,
  `unmask`, image resampling, mask computation internals, and `signal.clean`
  details outside masker estimators.
- Use [surface-workflows](../surface-workflows/SKILL.md) for detailed
  `SurfaceImage`, mesh, hemisphere, and volume-to-surface concerns; this
  sub-skill only summarizes surface masker families.
- Use `../ml-decoding-connectivity/SKILL.md` after extraction when the next
  task is connectivity matrices, decoding, searchlight, decomposition, or
  downstream scikit-learn modeling.
- Use `../plotting-reporting/SKILL.md` for figure styling, interactive views,
  GLM reports, browser export, or optional plotting backend setup.

## Fast Operating Rules

1. Treat a 4D input transform as `(n_scans, n_features)` and a 3D input
   transform as `(n_features,)` unless scikit-learn output configuration wraps
   it.
2. Fit before transform when a mask, atlas resampling, or report data must be
   established; `fit_transform()` is fine for one-shot extraction.
3. Pass `confounds` and `sample_mask` with the original scan count; for multi
   maskers pass one item per image.
4. Use `inverse_transform()` only with arrays whose columns match the fitted
   voxel/region/seed count, and provide `mask_img` for sphere inversions.
5. Prefer `reports=False` in automated smoke tests and enable reports only
   when the user wants HTML diagnostics.

## References

- [API Reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/smoke_maskers_regions.py)
