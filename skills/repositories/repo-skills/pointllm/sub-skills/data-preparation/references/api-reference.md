# Data API reference

The public data exports are re-exported by `pointllm.data` as
`ObjectPointCloudDataset`, `make_object_point_data_module`, `ModelNet`,
`load_objaverse_point_cloud`, `pc_norm`, and `farthest_point_sample`. The
following behavior is distilled from the inspected source; examples below are
conceptual and do not require the original checkout.

## `ObjectPointCloudDataset`

```python
ObjectPointCloudDataset(
    data_path=None,
    anno_path=None,
    tokenizer=None,
    pointnum=8192,
    split="train",
    conversation_types=None,
    use_color=True,
    data_args=None,
)
```

Behavior:

1. Loads `anno_path` as a JSON list and records the initial size.
2. `conversation_types=None` becomes `("simple_description",)`; records with
   another `conversation_type` are filtered out. A missing type is treated as
   `simple_description`.
3. If color is enabled, two known corrupted colored Objaverse IDs are filtered:
   `6760e543e1d645d5aaacd3803bcae524` and
   `b91c0711149d460a8004f9c06d3b7f38`. This is source behavior, not a general
   corruption detector.
4. If `data_args.data_debug_num > 0`, it keeps the first N filtered records and
   takes precedence over train/validation splitting.
5. Otherwise, when `data_args.split_train_val` is true, it uses a contiguous
   split: train is records before `int(split_ratio * length)`, and val is the
   remainder. The default ratio in `DataArguments` is `0.9`; the constructor
   itself does not validate that ratio.
6. `__len__` is the filtered record count. For a point-bearing record,
   `__getitem__` loads `<object_id>_<pointnum>.npy`, normalizes it, and returns
   point data as a float32 torch tensor. With `tokenizer=None`, the compact
   return is `{"point_clouds": tensor, "object_ids": object_id}`.
7. With a tokenizer, conversation preprocessing returns `input_ids` and
   `labels`; point-bearing examples also include `point_clouds`. The first
   conversation value must contain `<point>` for multimodal replacement.

`use_color=False` slices loaded arrays to `[:, :3]` before normalization is
returned. `use_color=True` retains all six columns. In either case the source
normalizes XYZ and preserves columns after XYZ.

## `make_object_point_data_module`

This factory expects a tokenizer and a `data_args` object with at least
`split_train_val`, `data_path`, `anno_path`, `pointnum`, `conversation_types`,
`use_color`, `data_debug_num`, `split_ratio`, and `point_backbone_config` (the
last is needed when tokenization is enabled). It returns a dictionary with
`train_dataset`, `eval_dataset`, and `data_collator`.

- `split_train_val=False`: `eval_dataset` is `None`.
- `split_train_val=True` and `data_debug_num > 0`: validation aliases the same
  training dataset object, intentionally making debug validation cheap.
- Otherwise validation is a separate `split="val"` dataset over the contiguous
  tail.

## Normalization and sampling

### `pc_norm(pc)` and `ObjectPointCloudDataset.pc_norm(pc)`

Input is `N x C` with XYZ in the first three columns. Compute
`centroid = mean(pc[:, :3], axis=0)`, subtract it from XYZ, then divide XYZ by
`max(sqrt(sum(xyz**2, axis=1)))`. Concatenate the untouched `pc[:, 3:]` back.
Thus colors/normals are not centered or scaled. The repository does not guard a
zero radius; validation should reject that input first.

### `pc_normalize(pc)`

Input is `N x 3` XYZ only. It performs the same centroid and maximum-radius
unit-sphere transform and returns XYZ. It is used by `ModelNet` before optional
height handling. Do not pass an `(N, 6)` array when the intent is to normalize
only coordinates.

### `farthest_point_sample(point, npoint)`

Input is `N x D`, with sampling distances computed from `point[:, :3]`. It
selects an initial random row, then repeatedly chooses the farthest row under
the running minimum squared distance. It returns an `npoint x D` NumPy array.
The implementation assumes `N > 0` and does not reject `npoint > N`; repeated
indices can then occur after all available points are selected. `ModelNet` calls
this only when `npoints < point_set.shape[0]`; otherwise it keeps all rows.
Sampling is nondeterministic unless the caller controls NumPy's RNG.

## `ModelNet`

```python
ModelNet(config_path, split, subset_nums=-1, use_color=False)
```

`config_path=None` resolves to the package's bundled ModelNet40 YAML. `split`
must be exactly `train` or `test`. The configured `DATA_PATH` must already
exist, and the split pickle must be present. `subset_nums > 0` chooses a
reproducible Python `random.sample` subset using seed 0, but point sampling and
training-order shuffling still use NumPy/random behavior elsewhere.

`__getitem__` returns:

```python
{
  "indice": int,
  "point_clouds": torch.FloatTensor,  # N x C after options
  "labels": int,
  "label_names": str,
}
```

For training, row order is shuffled in `__getitem__`; test order is retained.
`use_normals=False` drops columns after XYZ. `use_height=True` appends a height
column measured from the minimum Y coordinate. `use_color=True` appends zeros
matching the current feature width, so the final feature width is doubled; this
is a source compatibility behavior and should not be mistaken for RGB.

## `DataCollatorForPointTextDataset`

The collator receives tokenized instances with `input_ids` and `labels`.
It pads `input_ids` with `tokenizer.pad_token_id`, pads labels with `-100`, and
creates `attention_mask = input_ids != pad_token_id`. If the first instance has
`point_clouds`, it examines all point tensors:

- identical shapes: `torch.stack` into a batch tensor;
- differing shapes: return a Python list, preserving each tensor.

This means a malformed or mixed point count may not fail at collation time; use
validation and a fixed `pointnum` when the downstream point encoder expects a
rectangular batch.

## CLI smoke surfaces

The source data modules expose lightweight help/smoke entry points, but the
safe checks for this sub-skill are synthetic and do not require a tokenizer,
checkpoint, ModelNet pickle, network, or large dataset. If invoking a native
module CLI in a prepared environment, use `--help` or a tiny local fixture only;
do not use it to start training or evaluation.
