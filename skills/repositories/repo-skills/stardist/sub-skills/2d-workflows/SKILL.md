---
name: "2d-workflows"
description: "Use for StarDist 2D workflows: Config2D data contracts, training
  handoff, pretrained or local StarDist2D inference, normalization and axes,
  dense or sparse prediction, scaling, tiling, multiclass prediction, shape
  completion, threshold tuning, and block-wise large-image prediction."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# StarDist 2D workflows

Use this sub-skill to prepare, train, load, diagnose, or run a **2D**
`StarDist2D` model. Keep the image/label contract, model configuration,
normalization policy, and prediction parameters together in the handoff.

This route targets StarDist 0.9.2 at commit
e80c6de700693bc228ed3c9ba1dc19c3785667ee. Its required baseline is CPU
TensorFlow 2.x plus compiled CPU StarDist extensions. Network/model downloads,
OpenCL/gputools, CUDA, and external integrations are optional and must be
explicit.

## Route by intent

- Use [workflows](references/workflows.md) for ordered preparation, bounded
  training pseudocode, pretrained/local inference, threshold tuning, and
  handoff contracts.
- Use [api-reference](references/api-reference.md) for exact 0.9.2 signatures,
  defaults, model storage, input/output shapes, and export boundaries.
- Use [multiclass](references/multiclass.md) when `n_classes` is not `None` or
  each detected object needs a class.
- Use [large-data](references/large-data.md) for `n_tiles`, `scale`, chunked
  output, or `predict_instances_big`.
- Use [troubleshooting](references/troubleshooting.md) before changing axes,
  channels, normalization, thresholds, grids, blocks, or backends to recover
  from a failure.

Use [evaluation-geometry](../evaluation-geometry/SKILL.md) for standalone
geometry/NMS/matching. Use
[deployment-integration](../deployment-integration/SKILL.md) for console,
BioImage.IO, ROI, Fiji, and QuPath work. Do not use this sub-skill for 3D model
or ray selection. A `ZYX`/`ZYXC` volume is not a 2D image; select and document a
plane as `YX`/`YXC`, or use [3d-workflows](../3d-workflows/SKILL.md).

## Operating route

1. Establish shape, dtype, axes, channels, model source, normalization,
   resources, and acceptance checks. In 2D, images are `YX` or channel-last
   `YXC`; labels are integer `YX`, background `0`, and positive instance ids.
2. Inspect `model.config.axes`, `n_channel_in`, `n_rays`, `grid`, and
   `n_classes`. Never treat a successfully constructed untrained model as a
   substitute for failed pretrained/local weight loading.
3. Normalize exactly once. `normalizer=None` means already normalized; either
   supply normalized float data or a compatible `csbdeep.data.Normalizer` and
   record its statistics/channel policy.
4. Use bounded pseudocode only for training. Training changes checkpoints and
   logs, can consume substantial CPU/RAM, and is not bundled as a script here.
   Shape completion is a training choice, not an inference switch.
5. Start instance inference with default `sparse=True`. Use dense mode only for
   full maps/diagnostics; `return_predict=True` forces dense mode. Record
   probability/NMS thresholds, scale, and one tile count per input axis.
6. Escalate memory from spatial `n_tiles` to `predict_instances_big`. Big
   prediction additionally requires measured object-size bounds, sufficient
   context, grid-compatible blocks, and
   `min_overlap + 2*context < block_size`.
7. Verify label shape/dtype, polygon detail counts/finite values, and a known
   crop or fixture before batch use. Handoff model identity, config, axes,
   normalization, exact prediction options, output contract, optional-resource
   requirements, warnings, and unresolved suitability assumptions.

## Evidence boundary

Native evidence was distilled from relative repository paths:
`stardist/models/model2d.py`, `stardist/models/base.py`,
`stardist/models/__init__.py`, `stardist/big.py`, `stardist/data/__init__.py`,
`README.md`, the `examples/2D/` and relevant `examples/other2D/` notebooks, and
`tests/test_model2D.py`, `tests/test_stardist2D.py`, `tests/test_big.py`,
`tests/test_utils.py`, plus their 2D fixtures/loaders. These paths are evidence,
not runtime dependencies; the bundled operating files do not import repository
examples or tests.
