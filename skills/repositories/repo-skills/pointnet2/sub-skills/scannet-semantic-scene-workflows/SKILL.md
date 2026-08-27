---
name: scannet-semantic-scene-workflows
description: "ScanNet semantic scene parsing workflows for the PointNet2
  TensorFlow 1 repository: preprocessing, pickle layout, labels, training, and
  whole-scene evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ScanNet Semantic Scene Workflows

Use this sub-skill when the task is about PointNet2 ScanNet semantic scene parsing: preparing ScanNet inputs, validating `scannet_data_pointnet2` pickles, reasoning about label tables, constructing the legacy training command, or explaining whole-scene evaluation behavior.

Do not use this sub-skill for ModelNet classification or ShapeNetPart part segmentation except to mention that the same TensorFlow 1.x and PointNet++ custom-op constraints apply.

## Read first

1. [references/data-formats.md](references/data-formats.md) for the self-contained ScanNet pickle schema, raw preprocessing layout, class ids, and label-table rules.
2. [references/workflows.md](references/workflows.md) for preprocessing, training, random-block evaluation, virtual scans, and whole-scene evaluation recipes.
3. [references/troubleshooting.md](references/troubleshooting.md) when a command, loader, label map, raw-data path, or whole-scene run fails.

## Bundled helpers

- [scripts/validate_scannet_layout.py](scripts/validate_scannet_layout.py): validates `scannet_train.pickle` / `scannet_test.pickle`, raw ScanNet scene prerequisites, generated preprocessing `.npy` files, optional demo outputs, and V1/V2 label-table column choices.
- [scripts/smoke_scannet_loader.py](scripts/smoke_scannet_loader.py): creates or loads a tiny ScanNet-style pickle fixture and exercises the adapted random-block and whole-scene loader behavior.
- [scripts/build_scannet_command.py](scripts/build_scannet_command.py): emits shell commands for the legacy trainer and preprocessing/demo scripts without executing the original Python 2 code.

## Operating rules

- Treat the original ScanNet trainer and preprocessing scripts as reference-only legacy scripts. They require Python 2 syntax, TensorFlow 1.x, large external datasets, and for PointNet++ model execution normally require compiled TensorFlow custom ops.
- Use the bundled validator before recommending a training run. The trainer expects `data/scannet_data_pointnet2/scannet_train.pickle` and `scannet_test.pickle` to contain two sequential pickle objects: a list of `N x 3` XYZ arrays and a same-length list of `N` semantic-label arrays.
- Remember that ScanNet class id `0` is `unannotated`; the evaluation code excludes label `0` from accuracy metrics by checking `label > 0` and positive sample weight.
- For ScanNetV2, do not reuse the V1 TSV column assumptions blindly. The repository note says the raw-class and NYU40-class columns are shifted by one relative to the V1 table; validate with explicit column overrides.
- Keep raw preprocessing and `demo.py` guidance path-aware: those scripts expect external ScanNet downloads, a scene list, and writable output directories. Validate missing raw-data paths and demo outputs independently.
