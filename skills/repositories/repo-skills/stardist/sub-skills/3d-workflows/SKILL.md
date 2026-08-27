---
name: "3d-workflows"
description: "Route StarDist 3D users through Config3D, ray and anisotropy
  selection, volume data preparation, training, local or pretrained inference,
  thresholds, and bounded large-volume prediction."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# StarDist 3D workflows

Use this sub-skill for volumetric images, `Config3D`, `StarDist3D`, ray
factories, anisotropic microscopy, and 3D block inference. The required
baseline is CPU TensorFlow 2.x, StarDist, and its compiled CPU extensions.
CUDA TensorFlow and OpenCL/gputools are optional accelerators; a visible CUDA
device does not prove OpenCL availability. BioImage.IO, QuPath, and OBJ/export
are optional integrations, not part of the CPU baseline; their workflows belong
to [`deployment-integration`](../deployment-integration/SKILL.md).

## Route

1. Establish `ZYX`/`ZYXC` axes, channel count, label convention, physical
   anisotropy, and a memory budget.
2. Choose one ray object and make its length equal `Config3D.n_rays` and every
   distance tensor's final dimension.
3. Validate paired image/mask volumes, grid-compatible patches, normalization,
   and class mappings before training.
4. Load/build a local or pretrained model, then use the verified
   `StarDist3D.predict_instances` contract with deliberate sparse/dense,
   threshold, scale, and tiling choices.
5. Use `predict_instances_big` only after checking per-axis object-size and
   the strict constraint `min_overlap+2*context < block_size`; consult
   [`troubleshooting.md`](references/troubleshooting.md) for recovery.

Detailed contracts and recipes:

- [`api-reference.md`](references/api-reference.md): Config3D, data, model,
  prediction, training, and threshold APIs.
- [`workflows.md`](references/workflows.md): 3D preparation, training,
  pretrained/local inference, multiclass, normalization, and smoke routes.
- [`rays-and-anisotropy.md`](references/rays-and-anisotropy.md): ray factories,
  physical conventions, scaling, and `dist_loss_weights`.
- [`large-data.md`](references/large-data.md): `n_tiles`, block inference,
  `labels_out`, memory, and seam constraints.
- [`troubleshooting.md`](references/troubleshooting.md): install/import,
  backend, axes/rays/grid, model-path, threshold, tiling, and OOM recovery.

Native repository evidence for this sub-skill is recorded by relative path:
`stardist/models/model3d.py`, `stardist/models/base.py`, `stardist/rays3d.py`,
`stardist/big.py`, `stardist/geometry/geom3d.py`, `examples/3D/1_data.ipynb`,
`examples/3D/2_training.ipynb`, `examples/3D/3_prediction.ipynb`,
`examples/other3D/README.md`, `tests/test_model3D.py`,
`tests/test_stardist3D.py`, `tests/test_nms3D.py`, and `tests/test_big.py`.
These paths are provenance only; runtime use requires no source checkout.
