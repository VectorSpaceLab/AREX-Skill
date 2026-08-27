---
name: tracking-segmentation
description: "Plan and debug Dipy tractography, streamline clustering, bundle
  segmentation, brain masking, tissue classification, and tractometry handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dipy Tracking And Segmentation

Use this sub-skill when a task mentions tractography, streamlines, seeds, direction getters, stopping criteria, QuickBundles, RecoBundles, LabelsBundles, median Otsu masking, tissue classification, AFQ, BUAN, or tractometry. Keep this file as the router; detailed APIs, CLI commands, workflow recipes, and troubleshooting live in bundled references.

## Route First

- Need peaks, ODFs, SH coefficients, PAM creation, or diffusion model fitting before tracking: use `../reconstruction-models/`, then return here for tractography.
- Need tractogram load/save, `StatefulTractogram`, file formats, bvals/bvecs, reference image, space, origin, or bbox checks: use `../io-data/`.
- Need affine/SyN registration, SLR design, bundlewarp, or transform estimation: use `../registration-alignment/`.
- Need generic `dipy_*` entry-point discovery, workflow parser behavior, or help probing: use `../cli-workflows/`.

## Bundled Runtime References

- `references/api-reference.md` lists the tracking, segmentation, masking, tissue-classification, AFQ, BUAN, and owned CLI surfaces.
- `references/workflows.md` gives safe planning recipes for local tracking, PFT, streamline manipulation, QuickBundles, RecoBundles/LabelsBundles, masking, tissue classification, AFQ, and BUAN handoffs.
- `references/troubleshooting.md` maps common tracking/segmentation symptoms to likely causes, concrete recovery actions, validation checks, and routing boundaries.
- `scripts/dipy_streamline_smoke.py` runs deterministic synthetic `Streamlines`, `QuickBundles`, seed, and stopping-criterion checks without downloads or file writes.

## Safe Defaults

- Start with tiny synthetic arrays or a small already-local tractogram before whole-brain tracking, bundle recognition, or group BUAN analysis.
- Treat coordinates explicitly: seeds and streamline points live in the point space implied by the affine, while masks and stopping maps are voxel grids sampled through that affine.
- Prefer deterministic seed masks, fixed random seeds, bounded `minlen`/`maxlen`, and numeric checks before optional visualization.
- Do not assume FURY, matplotlib, PyTorch, TensorFlow, or neural-network model weights are available; use classic numeric and masking fallbacks when optional surfaces are absent.

## Minimal Validation

Run the bundled smoke script before deeper debugging:

```bash
python scripts/dipy_streamline_smoke.py
```

Expected output is JSON with `ok: true`, four synthetic streamlines, two clusters, nonzero seed count, zero empty-mask seeds, and positive streamline lengths.
