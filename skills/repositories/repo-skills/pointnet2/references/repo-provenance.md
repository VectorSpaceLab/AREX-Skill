# pointnet2 repo provenance

## Source snapshot

- Repository: `charlesq34/pointnet2`
- Upstream URL: `https://github.com/charlesq34/pointnet2.git`
- Commit: `42926632a3c33461aebfbee2d829098b30a23aaa`
- Branch: `master`
- Tag: none observed during construction
- License: MIT (`LICENSE`)
- Package metadata: no `setup.py`, `pyproject.toml`, `setup.cfg`, requirements file, or console-entry metadata was present. Treat this as a script-style research checkout.

## Dirty state at construction

The source checkout was dirty during skill construction, but no modified tracked source files were observed. The dirty entries were untracked generated/review artifacts under `skills/` and Python bytecode caches such as `*.pyc` and `__pycache__/`. Runtime guidance is based on the commit above plus the relative evidence paths below, not on generated artifacts or bytecode caches.

## Relative evidence paths used

| Area | Evidence paths |
|---|---|
| Public docs and license | `README.md`, `data/README.md`, `scannet/README.md`, `LICENSE` |
| ModelNet40 classification | `train.py`, `train_multi_gpu.py`, `evaluate.py`, `modelnet_dataset.py`, `modelnet_h5_dataset.py`, `models/pointnet2_cls_ssg.py`, `models/pointnet2_cls_msg.py`, `models/pointnet_cls_basic.py` |
| ShapeNetPart part segmentation | `part_seg/command.sh`, `part_seg/command_one_hot.sh`, `part_seg/train.py`, `part_seg/train_one_hot.py`, `part_seg/evaluate.py`, `part_seg/test.py`, `part_seg/part_dataset.py`, `part_seg/part_dataset_all_normal.py`, `models/pointnet2_part_seg.py`, `models/pointnet2_part_seg_msg_one_hot.py` |
| ScanNet semantic scene parsing | `scannet/train.py`, `scannet/scannet_dataset.py`, `scannet/scene_util.py`, `scannet/pc_util.py`, `scannet/preprocessing/collect_scannet_scenes.py`, `scannet/preprocessing/demo.py`, `scannet/preprocessing/fetch_label_names.py`, `scannet/preprocessing/scannet_util.py`, `scannet/preprocessing/scannet-labels.combined.tsv`, `models/pointnet2_sem_seg.py` |
| Shared model APIs and utilities | `utils/tf_util.py`, `utils/pointnet_util.py`, `utils/provider.py`, `utils/pc_util.py`, `utils/show3d_balls.py`, `utils/compile_render_balls_so.sh`, `utils/render_balls_so.cpp` |
| TensorFlow custom ops | `tf_ops/sampling/tf_sampling.py`, `tf_ops/sampling/tf_sampling.cpp`, `tf_ops/sampling/tf_sampling_g.cu`, `tf_ops/sampling/tf_sampling_compile.sh`, `tf_ops/grouping/tf_grouping.py`, `tf_ops/grouping/tf_grouping.cpp`, `tf_ops/grouping/tf_grouping_g.cu`, `tf_ops/grouping/tf_grouping_compile.sh`, `tf_ops/3d_interpolation/tf_interpolate.py`, `tf_ops/3d_interpolation/tf_interpolate.cpp`, `tf_ops/3d_interpolation/interpolate.cpp`, `tf_ops/3d_interpolation/tf_interpolate_compile.sh`, `tf_ops/*/*_op_test.py` |

## Excluded or non-portable material

- `.git/` metadata was used only through Git commands for the source snapshot.
- Generated skill output and review artifacts under `skills/` were not source evidence.
- Downloaded datasets under `data/` are external artifacts and are not shipped by this skill.
- Platform-specific binaries such as `tf_ops/3d_interpolation/tf_interpolate_so.so` were treated as source-checkout facts only; they are not portable runtime assets for the generated skill.
- Python bytecode caches (`*.pyc`, `__pycache__/`) were ignored.

## Runtime evidence summary

A private construction-time smoke check verified a Python 2.7 + TensorFlow 1.15 CPU environment for source imports, tiny data fixtures, utility checks, and the `pointnet_cls_basic` graph shape. Legacy CUDA custom-op execution was not proven because a matching CUDA/nvcc custom-op toolchain was unavailable. Keep that distinction when using this skill: CPU/static/data checks are verified; full PointNet++ GPU/custom-op execution remains backend-dependent.

## Staleness rule

If a future checkout is not at commit `42926632a3c33461aebfbee2d829098b30a23aaa`, re-check the relative evidence paths for changed CLI flags, dataset schemas, TensorFlow custom-op wrappers, and model signatures before relying on the generated commands or troubleshooting notes.
