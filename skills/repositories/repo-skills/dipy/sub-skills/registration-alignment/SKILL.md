---
name: registration-alignment
description: "Reslice Dipy images, configure affine and SyN registration, apply
  transforms, correct DWI motion, and align streamlines or bundles."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dipy Registration And Alignment

Use this sub-skill when a task involves Dipy spatial resampling, affine image registration, SyN/diffeomorphic registration, applying saved transforms, between-volume DWI motion correction, streamline linear registration, or BundleWarp bundle deformation. Keep this file as the router; detailed API choices, CLI recipes, and failure recovery live in the bundled references.

## Route Here For

- Reslicing or resampling 3D/4D image arrays to new voxel sizes with `dipy.align.reslice.reslice` or `dipy_reslice`.
- Choosing and configuring center-of-mass, translation, rigid, scaling, or affine image registration.
- Running SyN registration with CC, SSD, or EM metrics and saving/applying displacement fields.
- Applying affine `.txt` or diffeomorphic displacement-field transforms to images.
- Correcting between-volume DWI motion from a 4D image plus b-values/b-vectors.
- Running streamline linear registration (SLR) or BundleWarp when bundle geometry, not voxel data, is the registration target.

## Route Elsewhere

- NIfTI loading/saving, b-values/b-vectors, headers, tractogram reference handling, and format conversion: `../io-data/`.
- Tractography, streamline clustering, bundle recognition, segmentation outputs, and tractometry after alignment: `../tracking-segmentation/`.
- Generic Dipy CLI discovery, parser behavior, and cross-family command inventories: `../cli-workflows/`.
- Model fitting, peaks, ODFs, tensor maps, or DWI reconstruction before/after alignment: `../reconstruction-models/`.

## Bundled Runtime References

- `references/api-reference.md` summarizes the registration APIs, transform objects, metrics, and owned CLI entry points.
- `references/workflows.md` gives safe recipes for reslice, affine/SyN registration, transform application, motion correction, SLR, and BundleWarp.
- `references/troubleshooting.md` maps symptoms to causes, concrete recovery actions, and validation checks.
- `scripts/dipy_reslice_smoke.py` runs a deterministic tiny 3D reslice check and prints JSON.

## Safe Defaults

- Start with a small crop or synthetic array before full-resolution whole-volume registration.
- Preserve and validate affines: moving data is transformed into static/reference space, and saved aligned images should use the static affine.
- Prefer affine or rigid registration for global pose/scale mismatch; add SyN only when nonlinear anatomical deformation is scientifically justified.
- Avoid assuming `matplotlib`, FURY, or display backends are installed; visual overlays from `dipy.viz.regtools` are optional QA, not required for runtime validation.
- For labels or masks, use nearest-neighbor interpolation; for scalar anatomical images, linear interpolation is usually safer.

## Minimal Validation

Run the bundled smoke script before deeper debugging:

```bash
python scripts/dipy_reslice_smoke.py
```

Expected output is JSON with `ok: true`, a changed shape, a changed affine diagonal consistent with the target voxel size, and preserved value range for the tiny synthetic volume.
