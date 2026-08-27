# Configuration Loading, Merging, and Validation

## 1. Load without constructing

Use the bundled inspector first:

```bash
python scripts/inspect_config.py examples/point_pillars/configs/kitti_point_pillars_mghead_syncbn.py
python scripts/inspect_config.py examples/second/configs/kitti_car_vfev3_spmiddlefhd_rpn1_mghead_syncbn.py
python scripts/inspect_config.py examples/cbgs/configs/nusc_all_vfev3_spmiddleresnetfhd_rpn2_mghead_syncbn.py
```

The default mode reads Python source with `ast` and reports top-level sections,
string values for `type`, and model/task/anchor hints. It never executes the
config or imports Det3D model modules. `--execute-python` opts into the actual
`Config.fromfile` loader and remains non-constructive after loading; use it
only for trusted configs in an environment with the config's imports.

The actual loader has these consequences:

1. It expands the path and checks that it is a file.
2. For `.py`, it imports the module by basename, temporarily adding its parent
   directory to `sys.path`.
3. It copies every module global whose name does not start with `__` into the
   config dictionary. Imports and helper names can therefore appear as config
   entries.
4. For JSON/YAML it delegates to the file I/O layer. YAML support depends on
   the corresponding optional file-I/O dependency.

A Python config can call `build_box_coder`, compute `get_downsample_factor`,
create a logger, or derive `class_names`. Static inspection cannot resolve all
of those values. Report unresolved expressions rather than pretending they are
literal values.

## 2. “Merging” in this source

There is no general `_base_` inheritance, recursive merge, or command-line
config override implementation in `Config`. Compose configs with ordinary
Python imports/variables or edit a copy deliberately. The training CLI applies
specific assignments for `--work_dir` and `--resume_from`, and can scale
`lr_config.lr_max` with `--autoscale-lr`; those flags are not a general merge
engine. Evaluation reads the config and then sets test-mode behavior in the
workflow.

When making an overlay manually:

- preserve the original model family and registry type unless changing the
  full architecture;
- update derived values (`out_size_factor`, head channels, anchor ranges,
  post-center limits) together;
- preserve the class order used by dataset, tasks, anchors, and checkpoint;
- do not merge arbitrary dictionaries with an unreviewed `dict.update`, which
  can silently retain incompatible nested values;
- record changed paths and the reason for each change.

## 3. Required-value and path checks

For a train/evaluate-ready example, inspect these groups:

| Group | Checks |
| --- | --- |
| Dataset | `data.*.type`, `root_path`, info/annotation paths, class names, sweeps, and pipeline order |
| Geometry | `voxel_generator.range`, voxel size, max points/voxels, model input features |
| Classes | `tasks`, flattened `class_names`, anchor `class_name` values, dataset class names |
| Targets | `target_assigner`, similarity calculator, thresholds, sample size, box coder |
| Model | detector, reader, backbone/scatter, neck, head, channel counts, `pretrained` |
| Decode | NMS mode/limits, score threshold, post-center range, `max_per_img` |
| Runtime | optimizer, LR, checkpoint/log config, epochs, distributed backend, work dir |

Absolute dataset, checkpoint, and work paths are intentionally environment
specific. Validate existence and permissions in the user's environment; do not
replace them with paths from examples.

## 4. Tasks and anchors

The examples use a `tasks` list. Each task groups one or more class names:

```python
tasks = [
    dict(num_class=1, class_names=["Car"]),
    dict(num_class=2, class_names=["truck", "construction_vehicle"]),
]
```

The data `AssignTarget` pipeline slices the ordered anchor-generator list by
each task's `num_class`. Thus the number of anchor generators must equal the
sum of task `num_class` values, and each slice must use the same class order as
the corresponding task. `TargetAssigner.classes` comes from anchor generator
`class_name`, not from the model head.

The head derives per-task class counts from `len(task["class_names"])` and uses
two anchors per class when computing classification/regression channels. A
mismatched declared `num_class` can therefore fail later or silently create an
incompatible target partition; reject it during inspection.

The config spelling is `matched_threshold` and `unmatched_threshold`. The
builder passes those to generator fields named `match_threshold` and
`unmatch_threshold`. Preserve both the numerical values and the class mapping.

## 5. Spatial and channel validation

For the example-style models, the target assigner computes its feature map from
the voxel grid and `assigner.out_size_factor`. The helper used in the examples
is equivalent to:

```text
downsample = prod(neck.ds_layer_strides, default 1)
downsample /= last(neck.us_layer_strides) when any upsample strides
downsample *= backbone.ds_factor
out_size_factor = int(downsample)
```

Check it is positive and consistent with the actual sparse backbone. For `RPN`,
layer stride/filter/upsample lists must have matching lengths, and upsample
ratios must be mutually consistent. The RPN constructor logs through the
provided `logger`; the examples pass one, so a missing logger can fail during
construction.

Check `RPN` output channels against `MultiGroupHead.in_channels`. For a normal
RPN this is the sum of `us_num_filters`; for one output it is that single filter
count. Do not infer channels from a comment when the config values disagree.

## 6. Model-family examples

- PointPillars uses point pillars, `PillarFeatureNet`, a dense scatter, and an
  RPN. `PillarFeatureNet` decorates each point with cluster and pillar-center
  offsets and optionally distance; its `voxel_size` and `pc_range` must match
  voxelization.
- SECOND uses `VoxelNet` with `VoxelFeatureExtractorV3`, `SpMiddleFHD`, and an
  RPN in the example. This is the SECOND-style composition, not a detector
  called `SECOND`.
- CBGS uses `VoxelNet`, a multi-task class grouping, `SpMiddleResNetFHD`, and
  a nuScenes-style data pipeline. CBGS is represented by its config/data
  choices; it is not a separate detector registry entry.

## 7. Safe edit and approval checklist

Before applying an edit, save the static inspection output and answer:

- Does the config still parse, and are all dynamic expressions understood?
- Are class/task/anchor orders unchanged or intentionally migrated together?
- Are box coder `n_dim`, encoded `code_size`, head regression channels, and
  loss `code_weights` compatible?
- Are voxel range, voxel size, feature-map stride, NMS range, and dataset frame
  conventions aligned?
- Is the checkpoint known to match the resulting class order and architecture?
- Are spconv, CUDA extensions, and dataset SDKs available for the next stage?

A positive answer is a validation record, not evidence of a successful training
run.
