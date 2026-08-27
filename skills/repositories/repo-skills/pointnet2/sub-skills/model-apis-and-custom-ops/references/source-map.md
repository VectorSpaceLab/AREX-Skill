# Source map and verified facts

## Source evidence distilled

| Source artifact | Used for |
| --- | --- |
| `utils/tf_util.py` | TensorFlow 1.x variable helpers, conv/FC/pooling/batch-norm/dropout signatures, `tf.contrib` dependency. |
| `utils/pointnet_util.py` | Set abstraction, multi-scale grouping, feature propagation signatures and tensor shapes. This file is the implementation of the SA/FP APIs named in this sub-skill's responsibility. |
| `utils/provider.py` | Point-cloud augmentation, H5 helper behavior, Python 2 `xrange` compatibility issue. |
| `utils/pc_util.py` | Volume/image conversion, PLY I/O, software rendering, dependency requirements (`eulerangles`, `plyfile`). |
| `utils/show3d_balls.py` | Interactive OpenCV renderer behavior, top-level GUI/shared-library side effects, keyboard controls. |
| `utils/compile_render_balls_so.sh` | Renderer compile recipe adapted into `scripts/compile_render_balls_so.sh`. |
| `tf_ops/sampling/tf_sampling.py` | `tf_sampling_so.so` import path, sampling wrappers, gradient/no-gradient registrations. |
| `tf_ops/grouping/tf_grouping.py` | `tf_grouping_so.so` import path, ball-query/grouping/KNN wrapper APIs. |
| `tf_ops/3d_interpolation/tf_interpolate.py` | `tf_interpolate_so.so` import path, 3-NN/interpolation wrapper APIs and gradient. |
| `tf_ops/*/*_compile.sh` | CUDA 8 / TF1.2 / Python2.7 hard-coded compile assumptions and TF1.4 commented variants. |
| `tf_ops/*/*_op_test.py` | Optional native gradient/load verification candidates after compatible custom-op build. |
| `models/pointnet_cls_basic.py` | CPU baseline placeholders, model, loss, and verified output shape. |
| `models/pointnet2_cls_ssg.py`, `models/pointnet2_cls_msg.py` | Classification PointNet++ consumer shapes and SA/MSG layer stack. |
| `models/pointnet2_part_seg.py`, `models/pointnet2_part_seg_msg_one_hot.py` | Part-segmentation consumer shapes and FP stack. |
| `models/pointnet2_sem_seg.py` | ScanNet semantic segmentation consumer shapes, FP stack, weighted loss. |

## Verified compatibility facts distilled into this sub-skill

- TensorFlow 1.15.0 CPU plus the legacy scientific stack can support the CPU baseline and source-level API inspection path.
- `provider`, `modelnet_dataset`, `part_dataset_all_normal`, `scannet_dataset`, `tf_util`, and `pointnet_cls_basic` can be loaded under a legacy-compatible inspection setup.
- Tiny-fixture smoke checks passed for ModelNet-style, ShapeNetPart-style, and ScanNet-style data-loader behavior.
- `pointnet_cls_basic` built a TensorFlow graph with output shape `[2, 40]`.

## Verification status and limits represented in this skill

- CPU baseline graph guidance is anchored as a safe/alternative verification candidate.
- NumPy geometry utilities are represented with a tiny-array smoke script and explicit dependency checks.
- TensorFlow custom-op scripts are represented as readiness inspection and compile guidance, not as a claim that a future environment already has a compatible CUDA/nvcc/TF ABI.
- Original TensorFlow custom-op tests remain optional native candidates because they require compiled `.so` files and a compatible legacy backend.
- Workflow-specific trainers are intentionally out of this runtime subtree; they should link here only for shared API/custom-op troubleshooting.
