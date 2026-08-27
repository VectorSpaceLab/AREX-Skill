# pointnet2 workflow map

Use this map after the root `SKILL.md` identifies the request as repo-specific PointNet2 work.

## Read order

1. Run or reason through the shared readiness check: `scripts/check_pointnet2_env.py`.
2. Pick the workflow owner from the table below.
3. If the selected workflow touches PointNet++ models, also check custom-op readiness through `sub-skills/model-apis-and-custom-ops/` before claiming native execution is available.
4. Keep dataset layout validation separate from native TensorFlow/CUDA verification; data validators do not require the PointNet++ custom ops.

## Intent-to-owner map

| Signals in the user request | Owner | Helper scripts to prefer |
|---|---|---|
| `ModelNet40`, classification, `train.py`, `train_multi_gpu.py`, `evaluate.py`, checkpoint restore, voting, `pointnet2_cls_ssg`, `pointnet2_cls_msg` | [classification-workflows](../sub-skills/classification-workflows/) | `sub-skills/classification-workflows/scripts/build_classification_command.py`, `sub-skills/classification-workflows/scripts/validate_modelnet_layout.py`, `sub-skills/classification-workflows/scripts/smoke_modelnet_loader.py` |
| `ShapeNetPart`, part segmentation, `part_seg`, `train_one_hot.py`, category conditioning, part-label ranges, legacy visualization/test path | [part-segmentation-workflows](../sub-skills/part-segmentation-workflows/) | `sub-skills/part-segmentation-workflows/scripts/build_part_seg_command.py`, `sub-skills/part-segmentation-workflows/scripts/validate_shapenetpart_layout.py`, `sub-skills/part-segmentation-workflows/scripts/smoke_shapenetpart_loader.py` |
| `ScanNet`, semantic scene parsing, `scannet_train.pickle`, raw scene preprocessing, label TSV columns, whole-scene evaluation, virtual scans | [scannet-semantic-scene-workflows](../sub-skills/scannet-semantic-scene-workflows/) | `sub-skills/scannet-semantic-scene-workflows/scripts/build_scannet_command.py`, `sub-skills/scannet-semantic-scene-workflows/scripts/validate_scannet_layout.py`, `sub-skills/scannet-semantic-scene-workflows/scripts/smoke_scannet_loader.py` |
| `tf_ops`, `tf_sampling`, `tf_grouping`, `tf_interpolate`, `pointnet_util`, `tf_util`, `pointnet_cls_basic`, geometry utilities, renderer build, TensorFlow import/custom-op errors | [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) | `sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py`, `sub-skills/model-apis-and-custom-ops/scripts/smoke_pointnet_baseline.py`, `sub-skills/model-apis-and-custom-ops/scripts/smoke_geometry_utils.py`, `sub-skills/model-apis-and-custom-ops/scripts/compile_render_balls_so.sh` |

## Cross-workflow sequences

### PointNet++ classification plus custom-op troubleshooting

1. Use [classification-workflows](../sub-skills/classification-workflows/) to decide HDF5 vs normal-resampled ModelNet40 data, `pointnet2_cls_ssg` vs `pointnet2_cls_msg`, checkpoint/dump paths, and command flags.
2. Use [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) to inspect TensorFlow 1.x and `tf_ops` library readiness.
3. If custom ops are absent or ABI-broken, keep classification guidance at command/data planning level and report the backend block instead of running `train.py` or `evaluate.py` as if the backend were ready.

### ShapeNetPart and ScanNet data preparation

1. Use [part-segmentation-workflows](../sub-skills/part-segmentation-workflows/) for `synsetoffset2category.txt`, split JSON, normal text files, legacy `points/points_label`, one-hot category-label rules, and the ShapeNetPart validator.
2. Use [scannet-semantic-scene-workflows](../sub-skills/scannet-semantic-scene-workflows/) for `scannet_train.pickle` / `scannet_test.pickle`, raw scene prerequisites, label TSV columns, preprocessing outputs, and the ScanNet validator.
3. Do not merge the two schemas: ShapeNetPart part labels and ScanNet semantic labels have different file contracts and validation failure modes.

### Safe CPU smoke or API-only request

Route directly to [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/). The CPU baseline `pointnet_cls_basic` can be smoke-checked without PointNet++ custom ops, but it still uses TensorFlow 1.x semantics.

## When to return to root troubleshooting

Use [troubleshooting.md](troubleshooting.md) before sub-skill details when the user reports only a generic failure such as `SyntaxError`, missing `tf.contrib`, missing `*_so.so`, `nvcc` not found, unexpected dataset download, missing `eulerangles`/`plyfile`, or headless visualization errors.
