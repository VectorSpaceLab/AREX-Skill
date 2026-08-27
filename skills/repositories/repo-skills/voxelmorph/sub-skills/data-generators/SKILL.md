---
name: data-generators
description: "Use VoxelMorph volume I/O, npz/NIfTI/MGZ data conventions,
  segmentation utilities, metric helpers, and NumPy data generators for
  registration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Generators

Use this sub-skill when a task is about preparing, validating, loading, or selecting data streams for VoxelMorph workflows before model-specific training or transform math begins.

## Route here for

- Reading or writing volumes with `voxelmorph.py.utils.load_volfile()` and `save_volfile()`.
- Explaining `.npz`, `.npy`, NIfTI, and MGZ conventions, including `vol` and optional `seg` keys.
- Building image lists, pair lists, phenotype CSV maps, label lists, atlas arrays, and segmentation inputs.
- Choosing a generator from `voxelmorph.py.generators` for scan-to-scan, scan-to-atlas, semisupervised, template, surface, or SynthMorph workflows.
- Computing or checking segmentation helpers: Dice overlap, label filtering, largest-component cleanup, signed distance transforms, surface point clouds, and Jacobian determinant summaries.
- Validating user-provided `.npz` files without downloading data or running training.

## Route elsewhere

- PyTorch model construction, loss selection, checkpoints, and training loops: use `../pairwise-registration/SKILL.md`.
- Dense displacement, affine, coordinate, interpolation, integration, composition, and tensor-transform mathematics: use `transform-ops`.
- Real dataset acquisition, clinical preprocessing, benchmark evaluation, or long-running training: out of scope unless the user supplies explicit data, runtime, and acceptance criteria.

## First decision

1. Identify the workflow target: scan-to-scan, scan-to-atlas, semisupervised labels, template creation, surface-distance learning, or SynthMorph label-map synthesis.
2. Confirm the data contract before writing any model code:
   - Volume arrays should have consistent spatial shape across a training list.
   - Standard `.npz` files should contain `vol`; semisupervised and surface workflows also need discrete integer `seg` arrays.
   - Generators add a batch axis first and usually add a feature axis last, yielding NumPy arrays shaped `(batch, *spatial, features)`.
   - NIfTI/MGZ loading uses nibabel; `.npz`/`.npy` loading does not carry affine metadata unless the caller separately manages it.
3. If the user supplies `.npz` files or a VoxelMorph image list, run the bundled validator before choosing a generator.

## Bundled references

- `references/api-reference.md` — signatures and behavioral notes for `voxelmorph.py.utils` and `voxelmorph.py.generators`, including generator yield structures.
- `references/data-formats.md` — volume, atlas, segmentation, label, list-file, affine, and README-derived data assumptions.
- `references/workflows.md` — generator-selection matrix and copyable recipes for scan-to-scan, scan-to-atlas, semisupervised, template, surface, and SynthMorph data streams.
- `references/troubleshooting.md` — symptoms, likely causes, and recovery steps for missing keys, shape mismatches, invalid labels, empty globs, and surface-generator edge cases.
- `scripts/validate_vxm_npz.py` — safe `.npz` validator for `vol`/`seg` keys, shape consistency, label dtypes, NaNs, and expected labels.

## Quick safe checks

From this sub-skill directory:

```bash
python scripts/validate_vxm_npz.py --help
python scripts/validate_vxm_npz.py data/*.npz --require-seg --allowed-labels 0,1,2,3
python scripts/validate_vxm_npz.py --file-list images.txt --prefix data/ --expect-shape 160,192,224
```

The validator reads only local files, writes nothing, performs no downloads, and exits non-zero on schema failures.

## Operating rules

- Keep data-generator work NumPy/file-schema focused. Hand off tensor conversion and model consumption to the pairwise-registration or transform-ops owners.
- Do not rely on legacy TensorFlow script paths or external tutorial downloads as runtime instructions. Distill the data contract into this skill instead.
- Prefer synthetic or user-supplied tiny fixtures for validation. Do not invent a requirement for OASIS, FreeSurfer, model weights, or private datasets.
- When users provide real NIfTI or MGZ files, validate shape and affine expectations with their own tools or a short local probe; this sub-skill's bundled validator intentionally targets `.npz` files only.
