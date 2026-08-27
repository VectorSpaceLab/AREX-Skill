# Troubleshooting

Use this reference when a custom dataset, transform, model component, runtime hook, or project
package refuses to build.

## 1) Registry or import errors

| Symptom | Likely cause | Fast fix |
| --- | --- | --- |
| `KeyError` / `AssertionError` that a type is not in the registry | The module was never imported or was registered in the wrong registry | Add the decorator, import the module package, and check the target registry name |
| `ModuleNotFoundError` from `custom_imports` | The imported string points at a class path, a typo, or a package that is not on the Python path | Import the module or package root, not the class name |
| A project class builds in one config but not another | The config lost the import or changed scope | Keep `custom_imports` and `default_scope` in the final config |

### Fast checks

- Verify the decorator matches the object type: `MODELS`, `DATASETS`, `TRANSFORMS`, `HOOKS`,
  `OPTIMIZERS`, or `TASK_UTILS`.
- Verify the config uses the exact class name.
- Verify the package exposes the module through its import tree.
- Use `allow_failed_imports=False` so missing imports fail loudly.

## 2) Config override mistakes

### Symptom

The inherited config still uses the old component, or a nested dict crashes when you replace one
field.

### Likely cause

The new dict is merged into the old one instead of replacing it.

### Fix

Use `_delete_=True` when you want to replace a nested structure rather than merge into it.
Also check the order of `_base_` files and make sure the final config still contains the project or
module import.

## 3) Dataset and annotation mismatches

| Symptom | Likely cause | Fast fix |
| --- | --- | --- |
| Wrong category mapping or strange label counts | `METAINFO['classes']`, config classes, and annotation order do not match | Align all three class orders |
| Empty samples crash parsing | The dataset class does not handle empty annotations | Return an empty `ann_info` with valid empty arrays or box containers |
| Boxes are shifted or rotated incorrectly | `box_type_3d` does not match the annotation coordinate system | Use the correct box type and conversion path |
| Custom dataset builds but evaluation looks wrong | The metric choice does not match the annotation format | Check the evaluator and the dataset format together |
| Pipeline loads points but later steps fail | `load_dim`, `use_dim`, or `data_prefix` are inconsistent | Recheck the point file format and pipeline assumptions |

### Dataset-specific reminders

- `Det3DDataset` is the right base when the dataset follows the standard 3D annotation flow.
- `parse_ann_info` should produce the keys expected by the rest of the pipeline.
- If the dataset is image-based or multi-modal, the calibration and image-prefix keys must be present
  in the sample dict.

## 4) Transform contract problems

### Symptom

A later pipeline step raises a `KeyError`, or tensor lengths stop matching after augmentation.

### Likely cause

The custom transform changed a key without updating the companion keys that depend on it.

### Fix

Keep the transform contract explicit:

- preserve `points`, `img`, `gt_bboxes_3d`, `gt_labels_3d`, and mask keys when later steps still need
  them;
- update `pcd_rotation`, `pcd_rotation_angle`, `pcd_scale_factor`, `pcd_trans`, and flip flags when
  geometry changes;
- if the project uses an augmentation matrix such as `lidar_aug_matrix`, update that too;
- check that the output still matches the packer input.

### Useful sanity check

If the transform is supposed to be a pure flag or metadata update, make sure it does not silently
change the sample geometry.

## 5) Model shape and channel mismatches

| Symptom | Likely cause | Fast fix |
| --- | --- | --- |
| `RuntimeError` from convolution or linear layers | `in_channels` or `out_channels` does not match the previous stage | Recompute the channel flow before wiring the config |
| Shape mismatch after voxelization | `point_cloud_range`, `voxel_size`, and middle-encoder output shape are inconsistent | Recalculate the grid and update dependent shapes |
| Head build fails on class count | `num_classes` does not match the dataset class list | Align the dataset metadata and the head config |
| Anchor-based head behaves strangely | Anchor ranges or sizes were copied from another dataset | Refit anchor settings to the new data |

### Quick rule

If a model component consumes a tensor created by another component, write down the exact tensor
shape before editing the config.

## 6) Runtime and hook issues

| Symptom | Likely cause | Fast fix |
| --- | --- | --- |
| Custom hook never fires | The hook is not registered or the priority is wrong | Register it in `HOOKS` and add it to `custom_hooks` |
| Optimizer config is ignored | The optimizer lives in the wrong registry or the wrapper constructor is missing | Check `OPTIMIZERS` and `OPTIM_WRAPPER_CONSTRUCTORS` |
| Scheduler steps at the wrong time | `by_epoch`, `begin`, or `end` is inconsistent with the loop type | Match the scheduler to the loop |
| Visualization config has no effect | The hook is disabled or the visualizer/backends are not configured together | Check `default_hooks.visualization`, `visualizer`, and `vis_backends` |

## 7) Project extension issues

| Symptom | Likely cause | Fast fix |
| --- | --- | --- |
| Project imports fail only in a fresh environment | The project package is not installed or not on the Python path | Install the project package or point `custom_imports` at the package root |
| A project op cannot be imported | The optional build step was skipped | Follow the project-specific build note or keep the project reference-only |
| A project-only config looks like a core-package config | The project package was flattened into the wrong place | Keep the extension inside `projects/` and import it explicitly |

## 8) Minimal debug sequence

Use this order before attempting a larger run:

1. Import the package or module.
2. Build the object from a tiny config.
3. Check the printed class name and registry target.
4. Inspect tensor shapes or dataset metadata.
5. Only then move to a longer train or eval command.

If any step fails, fix the smallest broken link first instead of editing multiple files at once.
