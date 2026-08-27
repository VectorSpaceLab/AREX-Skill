---
name: pointnet2
description: "Route PointNet2 TensorFlow 1 workflows across classification, part
  segmentation, ScanNet, and custom-op/API guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: pointnet2
  source-repo: charlesq34/pointnet2
license: NOASSERTION
---

# pointnet2

Use this root skill for tasks about the `charlesq34/pointnet2` TensorFlow 1.x repository: ModelNet40 classification, ShapeNetPart part segmentation, ScanNet semantic scene parsing, PointNet++ custom operators, shared TensorFlow model APIs, and point-cloud utilities.

Do not use it as a generic PointNet/PointNet++ paper summary or for unrelated PyTorch reimplementations.

## Quick readiness

Work against an explicit PointNet2 checkout. The generated skill is self-contained, but the upstream project is a legacy script-style repository, not an installable Python package.

Minimum legacy stack:

- Python 2.7 plus TensorFlow 1.x. The construction smoke checks used TensorFlow 1.15 CPU; the upstream README says the original code was tested with TensorFlow 1.2 GPU, Python 2.7, Ubuntu 14.04, and CUDA-8-era custom-op compile scripts.
- `numpy`, `h5py`, `scipy`, `scikit-learn`, `matplotlib`, `Pillow`, and `plyfile` for the data and utility surfaces.
- Full PointNet++ train/eval/model execution additionally requires compiled TensorFlow custom ops and a matching CUDA/nvcc/TensorFlow ABI. TensorFlow import success alone is not custom-op readiness.

Minimal smoke from this skill directory:

```bash
python scripts/check_pointnet2_env.py --repo-root /path/to/pointnet2 --require tf1
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2 --require tensorflow
```

If a task is data-only, run the relevant bundled validator before importing original repo loaders; the ModelNet HDF5 loader can download data as a top-level side effect when its expected folder is missing.

## Route by user intent

| User intent | Route | First action |
|---|---|---|
| ModelNet40 classification training, multi-GPU training, checkpoint evaluation, voting, ModelNet layout, or classification command construction | [classification-workflows](sub-skills/classification-workflows/) | Pick HDF5 vs normal-resampled data, then use the command builder and ModelNet validator. |
| ShapeNetPart part segmentation, one-hot category conditioning, part labels, category splits, or legacy visualization/test path | [part-segmentation-workflows](sub-skills/part-segmentation-workflows/) | Validate ShapeNetPart layout and choose plain vs one-hot workflow before proposing a trainer command. |
| ScanNet semantic scene parsing, ScanNet pickle layout, label TSV columns, preprocessing, or whole-scene evaluation | [scannet-semantic-scene-workflows](sub-skills/scannet-semantic-scene-workflows/) | Validate pickles/raw scene prerequisites and label-map columns before training guidance. |
| TensorFlow model APIs, PointNet++ SA/MSG/FP blocks, `tf_ops` custom libraries, CPU `pointnet_cls_basic`, geometry utilities, or renderer helpers | [model-apis-and-custom-ops](sub-skills/model-apis-and-custom-ops/) | Check TensorFlow 1.x, distinguish custom-op presence/load readiness, then run the targeted smoke helper. |
| Cross-cutting Python/TensorFlow/custom-op/data/geometry failure with no workflow chosen yet | [references/troubleshooting.md](references/troubleshooting.md) | Diagnose the shared failure first, then route to the owning sub-skill. |

## Integrated multi-route cases

- **PointNet++ classification plus custom-op troubleshooting**: start in [classification-workflows](sub-skills/classification-workflows/) for ModelNet40 data, model choice, checkpoint, and command construction; then use [model-apis-and-custom-ops](sub-skills/model-apis-and-custom-ops/) for `tf_sampling`, `tf_grouping`, `tf_interpolate`, CUDA/nvcc, and ABI readiness. Do not claim PointNet++ native training is runnable until the custom-op path is proven.
- **ShapeNetPart plus ScanNet data preparation**: route to [part-segmentation-workflows](sub-skills/part-segmentation-workflows/) and [scannet-semantic-scene-workflows](sub-skills/scannet-semantic-scene-workflows/) separately. Their validators cover different schemas; GPU/custom-op readiness is only needed for later model execution, not for layout checks.

## Root references

- [references/workflow-map.md](references/workflow-map.md): route map and cross-workflow read order.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting legacy Python, TensorFlow 1.x, custom-op, dataset, and geometry failures.
- [references/repo-provenance.md](references/repo-provenance.md): source snapshot, dirty-state summary, and relative evidence paths.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured router metadata for repo-skill import.
- [scripts/check_pointnet2_env.py](scripts/check_pointnet2_env.py): shared source-layout, dependency, TensorFlow, custom-op, and dataset readiness check.

## Hard limits to preserve

- This repo mixes Python 2 syntax, TensorFlow 1.x APIs, and CUDA-era custom-op compile assumptions. Python 3 or TensorFlow 2 import success is not sufficient proof of workflow readiness.
- Downloaded datasets and trained checkpoints are external to this generated skill. The skill describes layouts and provides validators; it does not ship ModelNet40, ShapeNetPart, ScanNet, or checkpoints.
- Raw training/evaluation scripts are treated as legacy source workflows. Prefer the bundled command builders and validators before asking a user to run original scripts.
