---
name: "deployment-integration"
description: "Route StarDist file prediction, local-model loading, BioImage.IO
  packaging, ImageJ ROI export, 3D OBJ export, and QuPath annotation handoff
  without assuming a source checkout."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Deployment and integration

Use this sub-skill when a StarDist model is used from a console, moved as a
model directory or BioImage.IO package, or handed to ImageJ/Fiji, a mesh
viewer, or QuPath. It covers integration boundaries, not model design,
training, or generic matching metrics.

## Route

- **Console file prediction:** read [cli-reference.md](references/cli-reference.md),
  then use the bundled `scripts/predict2d.py` or `scripts/predict3d.py`, or the
  installed `stardist-predict2d` / `stardist-predict3d` entry points.
- **Model loading, prediction semantics, training, or large blocks:** route to
  [2D workflows](../2d-workflows/SKILL.md) or [3D workflows](../3d-workflows/SKILL.md).
- **2D ROI or 3D mesh output:** read [export-formats.md](references/export-formats.md).
- **BioImage.IO conversion:** read [bioimageio.md](references/bioimageio.md).
  It is optional and can require network, temporary disk, and package-version
  compatibility; it is not the CPU baseline.
- **QuPath annotations:** read [qupath.md](references/qupath.md), then run the
  bundled Groovy script only inside QuPath. It is not a Python or generic
  Groovy command.
- **Any failure:** use [troubleshooting.md](references/troubleshooting.md)
  before changing axes, normalization, thresholds, or model files.

## Required baseline and safety contract

The required runtime is CPU Python/TensorFlow 2.x plus StarDist's compiled CPU
extensions. CUDA/TensorFlow acceleration, OpenCL/gputools, BioImage.IO,
ImageJ/Fiji, and QuPath are optional and must be declared explicitly. The
bundled Python scripts delay package imports until after argument and path
validation, so `--help` works from an unrelated cwd without importing a source
checkout or optional package.

For every run:

1. State dimensionality and axes. Use `YX`/`YXC` for 2D and `ZYX`/`ZYXC` for
   3D unless the declared permutation is intentional. A channel axis is not a
   batch or time axis.
2. Normalize with the model's intended convention. The bundled CLIs use
   per-image `csbdeep.normalize` with `pmin=1`, `pmax=99.8` by default; this is
   preprocessing, not `prob_thresh` or `nms_thresh`.
3. Resolve `--model` safely. An existing directory is local; a plain
   registered name may download/cache a pretrained model. A missing path-like
   selector is an error, not permission to guess.
4. Write only integer label TIFFs to a selected output directory. Reject path
   traversal, symlink escapes, duplicate names, input overwrite, and existing
   outputs unless `--overwrite` was consciously selected.
5. Verify handoff artifacts: inspect label shape/dtype, ROI ZIP members, OBJ
   `v`/`f` records, or BioImage.IO metadata. Record external GUI/network skips.

## Evidence and native candidates

Facts were distilled from relative repository evidence `stardist/scripts/`,
`stardist/bioimageio_utils.py`, `stardist/utils.py`,
`stardist/geometry/geom3d.py`, `extras/qupath_export_annotations.groovy`,
`README.md`, `examples/other2D/README.md`, `tests/test_bioimageio.py`,
`tests/test_model2D.py`, and `tests/test_model3D.py`. The verified live API
signature for both `StarDist2D.predict_instances` and
`StarDist3D.predict_instances` is:

```text
(self, img, axes=None, normalizer=None, sparse=True, prob_thresh=None,
 nms_thresh=None, scale=None, n_tiles=None, show_tile_progress=True,
 verbose=False, return_labels=True, predict_kwargs=None, nms_kwargs=None,
 overlap_label=None, return_predict=False)
```

Strict candidates are both bundled script `--help` checks from an arbitrary
cwd, static privacy/path checks, and bounded ROI/OBJ checks with synthetic or
prepared model data. BioImage.IO is run only if its optional dependency is
already available and bounded. QuPath is static/manual only unless an external
GUI environment is deliberately prepared.
