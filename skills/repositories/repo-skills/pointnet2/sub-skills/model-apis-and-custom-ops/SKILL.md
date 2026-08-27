---
name: model-apis-and-custom-ops
description: "Shared PointNet2 TensorFlow layer APIs, PointNet++
  set-abstraction/feature-propagation blocks, point-cloud utilities, custom-op
  readiness, visualization helper build notes, and the CPU PointNet baseline."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: pointnet2
  responsibility: shared-model-apis-custom-ops
license: NOASSERTION
---

# model-apis-and-custom-ops

Use this sub-skill when the task is about PointNet2's shared TensorFlow model-building APIs, custom TensorFlow operators, point-cloud geometry utilities, visualization helpers, or the CPU-safe `pointnet_cls_basic` baseline.

## Use this route for

- Building or modifying TensorFlow 1.x layer stacks that use `utils/tf_util.py` wrappers.
- Understanding `pointnet_util.py` set-abstraction (`SA`), multi-scale grouping (`MSG`), and feature-propagation (`FP`) call patterns used by PointNet++ models.
- Checking whether `tf_sampling_so.so`, `tf_grouping_so.so`, and `tf_interpolate_so.so` exist and can be loaded.
- Running a CPU-only graph smoke for `models/pointnet_cls_basic.py`.
- Using or debugging `utils/provider.py`, `utils/pc_util.py`, `utils/show3d_balls.py`, and `render_balls_so.so`.
- Explaining why TensorFlow import success is not the same as PointNet++ custom-op readiness.

## Do not use this route for

- ModelNet40 training/evaluation command construction. Use `../classification-workflows/`.
- ShapeNetPart training, evaluation, or dataset layout checks. Use `../part-segmentation-workflows/`.
- ScanNet preprocessing, pickle layout, or semantic scene workflows. Use `../scannet-semantic-scene-workflows/`.
- Full legacy GPU training as a native verification claim unless the custom-op backend has been separately prepared and proven.

## Read first

- `references/api-reference.md` for exact layer/model signatures, tensor shapes, and model consumer patterns.
- `references/custom-ops.md` for custom TensorFlow op names, `.so` locations, original compile assumptions, and health-check workflow.
- `references/utilities.md` for point-cloud augmentation, geometry conversion, PLY I/O, and visualization-helper behavior.
- `references/troubleshooting.md` for TensorFlow 1.x/TF2, missing dependency, ABI, missing `.so`, and renderer failure diagnoses.
- `references/source-map.md` for the source evidence and verified environment facts behind this sub-skill.

## Skill-owned scripts

- `scripts/inspect_custom_ops.py` — reports TensorFlow import state, expected custom-op files, optional `tf.load_op_library` results, `nvcc`/`g++` availability, and portable compile hints.
- `scripts/smoke_pointnet_baseline.py` — imports the checkout's `pointnet_cls_basic`, builds a `[batch_size, 40]` TF1 CPU graph, and optionally runs one session step.
- `scripts/smoke_geometry_utils.py` — runs deterministic tiny-array checks for provider/geometry helpers and separates missing `eulerangles`/`plyfile` dependencies from real data-shape failures.
- `scripts/compile_render_balls_so.sh` — safe wrapper around the renderer build recipe for `utils/render_balls_so.cpp`; supports `--dry-run` and explicit source/output paths.

## Typical workflows

Run these examples from the `pointnet2` skill root so the skill-owned script paths resolve.

### CPU-safe baseline graph

```bash
python sub-skills/model-apis-and-custom-ops/scripts/smoke_pointnet_baseline.py \
  --repo-root /path/to/pointnet2 --batch-size 2 --num-point 16
```

Expected success signal: TensorFlow 1.x with `tf.contrib` imports, `pointnet_cls_basic.get_model()` builds, and the output tensor/static shape is `[2, 40]`. This baseline does **not** require PointNet++ custom ops.

### Custom-op readiness check

```bash
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py \
  --repo-root /path/to/pointnet2 --require tensorflow
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py \
  --repo-root /path/to/pointnet2 --try-load --require custom-ops
```

Use the first command to prove TensorFlow metadata. Use the second only when the `.so` files are expected to exist; it distinguishes missing libraries, load/ABI errors, and TensorFlow-only success.

### Geometry utility smoke

```bash
python sub-skills/model-apis-and-custom-ops/scripts/smoke_geometry_utils.py \
  --repo-root /path/to/pointnet2
```

Expected success signal: provider transformations preserve expected shapes and point-cloud conversions/PLY round-trip work. If `eulerangles` or `plyfile` is missing, fix those packages before treating failures as data-shape errors.

### Renderer compile helper

```bash
bash sub-skills/model-apis-and-custom-ops/scripts/compile_render_balls_so.sh \
  --repo-root /path/to/pointnet2 --dry-run
bash sub-skills/model-apis-and-custom-ops/scripts/compile_render_balls_so.sh \
  --repo-root /path/to/pointnet2 --out-dir /path/to/pointnet2/utils
```

The helper builds only `render_balls_so.so` for `show3d_balls.py`; it does not build the TensorFlow PointNet++ ops.

## Verification anchors

- `pointnet-basic-model-graph`: CPU/TF1 graph build for `models/pointnet_cls_basic.py`, expected output shape `[B, 40]`.
- `point-cloud-utility-smoke`: NumPy/geometry helper smoke on tiny arrays.
- `custom-op-op-tests`: optional native tests under `tf_ops/*/*_op_test.py`, only after compatible compiled ops exist.
- `pointnet2-custom-op-model-graphs`: optional PointNet++ graph builds that require custom-op import success.

## Cross-links for consumers

- Classification PointNet++ models (`pointnet2_cls_ssg`, `pointnet2_cls_msg`) consume `pointnet_sa_module`, `pointnet_sa_module_msg`, `tf_util.fully_connected`, and `tf_util.dropout`; route command/data questions to `../classification-workflows/`.
- Part segmentation models consume `pointnet_sa_module`, `pointnet_fp_module`, and normal-aware point clouds; route ShapeNetPart data/workflow questions to `../part-segmentation-workflows/`.
- ScanNet semantic segmentation consumes `pointnet_sa_module`, `pointnet_fp_module`, and weighted sparse softmax loss; route ScanNet data/preprocessing questions to `../scannet-semantic-scene-workflows/`.

## Hard limits to keep explicit

- The repository is TensorFlow 1.x-era code. `tf.contrib` is required for the provided batch norm and Xavier initializer paths.
- The Python wrappers in `tf_ops/*` call `tf.load_op_library(...)` at import time; a missing `.so` blocks PointNet++ models before graph construction.
- Original custom-op compile scripts hard-code CUDA 8.0 and Python 2.7 TensorFlow include paths. Modern CUDA drivers/GPU visibility do not prove ABI compatibility.
- `show3d_balls.py` opens an OpenCV window and loads `render_balls_so` at import time; do not import it blindly in headless environments.
