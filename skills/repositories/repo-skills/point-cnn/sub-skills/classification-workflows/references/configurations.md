# Classification configuration matrix

The checked-in classification settings are Python modules under `pointcnn_cls`. The trainer imports the model named by `-m`, appends that model directory to `sys.path`, and imports the setting named by `-x`. The ordinary pair is therefore `-m pointcnn_cls -x <setting>`. Keep the model and setting from the same legacy PointCNN code version.

## Dataset-facing settings

| Dataset | Setting | Classes | Points sampled | Batch | Data width | Extra-feature mode | Notes |
|---|---|---:|---:|---:|---:|---|---|
| ModelNet40 | `modelnet_x3_l4` | 40 | 1024 | 128 | 6 | normals are loaded but not fed as extra features | four X-Conv layers; X transformation enabled |
| ModelNet40 | `modelnet_x3_l4_aligned` | 40 | 1024 | 128 | 6 | no extra features | small rotation range; X transformation enabled |
| ModelNet40 | `modelnet_x3_l4_aligned_w_fts` | 40 | 1024 | 128 | 6 | normals fed as extra features | `with_normal_feature=True` |
| ModelNet40 | `modelnet_x3_l4_w_fts` | 40 | 1024 | 128 | 6 | normals fed as extra features | larger rotation range; `with_normal_feature=True` |
| ModelNet40 | `modelnet_x3_l4_no_X` | 40 | 1024 | 128 | 6 | no extra features | X transformation disabled |
| ModelNet40 | `modelnet_x3_l4_no_X_wider` | 40 | 1024 | 128 | 6 | no extra features | wider channels; X transformation disabled |
| ModelNet40 | `modelnet_x3_l4_yxz` | 40 | 1024 | 128 | 6 | no extra features | `sorting_method='cyxz'` despite the setting name |
| ModelNet40 | `modelnet_x3_l5_no_X` | 40 | 1024 | 128 | 6 | no extra features | five X-Conv layers; X transformation disabled |
| ScanNet objects | `scannet_x2_l4` | 17 | 1024 | 128 | 6 | RGB remains an unused feature tensor | prepared conversion emits XYZ+RGB |
| TU-Berlin | `tu_berlin_x3_l4` | 250 | 512 | 200 | 6 | normals are not passed as extra features | three-fold conversion route; 512-point sketches |
| Quick Draw | `quick_draw_full_x2_l6` | 345 | 512 | 256 | 6 | normals are not passed as extra features | NPZ stroke loader and Python mapping; high RAM |
| MNIST | `mnist_x2_l4` | 10 | 160 | 256 | 4 | scalar pixel channel is passed as extra feature | four channels are XYZ + pixel feature |
| CIFAR-10 | `cifar10_x3_l4` | 10 | 512 | 200 | 6 | RGB channels are passed as extra features | six channels are XYZ + RGB |

These are defaults, not benchmark recommendations. The `--epochs` and `--batch_size` command-line values override setting values when supplied.

## Shared setting fields

A standard HDF5 setting defines:

- `load_fn`: normally `data_utils.load_cls_train_val`, which loads two file lists and shuffles the training pair.
- `balance_fn`: `None` in all checked-in classification settings; if enabled, training samples are repeated and epoch count is rescaled.
- `map_fn`: `None` for HDF5 datasets. Quick Draw maps padded strokes to point/normal tensors on the `tf.data` pipeline.
- `keep_remainder`: `True` in the checked-in settings. `False` uses `tf.contrib.data.batch_and_drop_remainder`.
- `num_class`, `sample_num`, schedule, optimizer and learning-rate fields.
- `rotation_range`, `rotation_range_val`, `scaling_range`, `scaling_range_val`, `jitter`, `jitter_val`, and `rotation_order`.
- `xconv_params`, `with_global`, `fc_params`, `sampling`, `data_dim`, `use_extra_features`, `with_normal_feature`, `with_X_transformation`, and optional `sorting_method`.

`xconv_params` is a list of dictionaries with keys `K`, `D`, `P`, `C`, and `links`; the setting's `x` multiplier controls channel widths in the supplied configurations. Detailed operator semantics belong to `core-xconv-and-operators`.

## Known configuration hazard

`quick_draw_full_x2_l6.py` defines `order = 'rxyz'`, while `train_val_cls.py` reads `setting.rotation_order`. As written at this source revision, Quick Draw reaches an attribute error before graph execution unless the setting is corrected in a local copy to define `rotation_order` (or the trainer is explicitly adapted). Treat that as a source-level compatibility fix, not as evidence that Quick Draw training passed. Keep the local modification documented with the run.

The README's historical ScanNet command names a setting that is not present in this checkout. Use `scannet_x2_l4`, which is the available classification setting, and verify the name with the validator or `py_compile` before starting a run.

## Data-width rule

`data_utils.load_cls` reads `data` and, when present, appends `normal` on the final dimension. The resulting width must equal the selected setting's `data_dim`. The trainer always treats the first three channels as XYZ. If `use_extra_features` is false, remaining channels still must exist at the declared width but are not passed to the model. Do not use a normals file with a 4-channel MNIST setting or a 4-channel data tensor with a 6-channel setting.
