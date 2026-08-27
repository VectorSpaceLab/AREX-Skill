---
name: io-data
description: "Load, validate, convert, and save Dipy diffusion images,
  gradients, tractograms, PAM files, and dataset inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dipy IO And Data

Use this sub-skill when a task starts from files or must preserve Dipy data metadata: NIfTI diffusion images, b-values/b-vectors, `GradientTable` objects, tractograms, `StatefulTractogram` objects, PAM5 peak files, fetched datasets, or IO conversion commands.

## Route Here For

- Loading/saving NIfTI arrays with affine, header, voxel-size, axis-code, and dtype decisions through `dipy.io.image`.
- Reading bvals/bvecs, constructing `dipy.core.gradients.gradient_table`, and validating DWI shape versus gradient count before fitting.
- Loading, constructing, converting, concatenating, and saving streamlines through `StatefulTractogram`, `load_tractogram`, and `save_tractogram`.
- Persisting and converting PAM5 peak files with `dipy.io.peaks` after reconstruction has produced peak arrays or `PeaksAndMetrics`.
- Listing or intentionally fetching bundled datasets through `dipy.data` or `dipy_fetch`.
- Using IO-oriented commands such as `dipy_info`, `dipy_fetch`, `dipy_split`, `dipy_extract_b0`, `dipy_extract_shell`, `dipy_extract_volume`, `dipy_math`, and conversion commands.

## Route Elsewhere

- Model fitting, ODF/SH/tensor computations, and creating peaks from a model: `../reconstruction-models/`.
- Tractography algorithms, stopping criteria, streamline clustering, segmentation, masks, and bundle analysis: `../tracking-segmentation/`.
- Global CLI parser mechanics, command inventory, and entry-point dispatch behavior: `../cli-workflows/`.
- Reslicing, registration transforms, motion correction, and spatial alignment workflows: `../registration-alignment/`.

## Use The Bundled Material

- `references/api-reference.md`: signatures, return values, and API-specific gotchas.
- `references/data-formats.md`: format, shape, affine/header, gradient, tractogram, and PAM5 invariants.
- `references/workflows.md`: practical IO recipes, validation order, dataset decisions, and command routing.
- `references/troubleshooting.md`: symptom-driven diagnostics for mismatches, references, bbox checks, PAM fields, and fetch failures.
- `scripts/dipy_io_probe.py`: safe no-network import/signature/gradient/tractogram probe with temporary writes only.

## Default Operating Pattern

1. Classify the input family: NIfTI image, bvals/bvecs, `GradientTable`, tractogram/SFT, PAM5, dataset fetcher, or IO CLI command.
2. Validate scientific consistency before handing off: DWI data should be 4D and `data.shape[-1]` must match `len(bvals)` and `bvecs.shape[0]`.
3. Preserve spatial metadata: keep the source affine, pass the source header when saving direct derivatives, and inspect voxel sizes/axis codes when orientation is uncertain.
4. For tractograms, choose a valid reference image/header, make `Space` and `Origin` explicit, and keep bbox validation enabled unless deliberately repairing invalid streamlines.
5. Use fresh output names or a temporary directory for conversions; avoid overwriting user inputs unless explicitly requested.
6. Treat `dipy_fetch list` and `FetchFlow.get_fetcher_datanames()` as safe discovery, but treat actual fetches as networked/cache-mutating operations requiring user intent.

## Safe Probe

Run the bundled helper from any project or temporary directory:

```bash
python scripts/dipy_io_probe.py --check-imports --check-signatures --tiny-gradient
python scripts/dipy_io_probe.py --tiny-tractogram --work-dir dipy-io-probe-output
```

The probe imports Dipy IO APIs, reports signatures, validates a tiny seven-volume gradient table, and can round-trip a one-streamline TRK file. It does not download datasets, run model fitting, or write outside its temporary directory unless `--work-dir` is provided.
