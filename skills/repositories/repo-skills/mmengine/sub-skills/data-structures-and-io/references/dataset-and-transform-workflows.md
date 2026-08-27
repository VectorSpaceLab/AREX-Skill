# Dataset and Transform Workflows

This reference distills MMEngine dataset, transform, sampler, and collate contracts for future agents implementing small or production data pipelines without reading the source repository.

## BaseDataset Contract

`BaseDataset` is a PyTorch-style dataset with MMEngine conventions for annotation loading, metadata priority, transform composition, subset handling, and serialized in-memory records.

Use this checklist for a custom dataset:

1. Decide whether the annotation file follows the OpenMMLab 2.0 format: a top-level mapping with `metainfo` and `data_list` keys.
2. Define `METAINFO` on the dataset class for stable class/task metadata, then let constructor `metainfo=` override it when users pass runtime metadata.
3. Implement `parse_data_info(raw_data_info)` when raw records need path joining, conversion, or expansion into multiple samples.
4. Override `load_data_list()` only when the annotation source is not the standard `metainfo` plus `data_list` mapping.
5. Override `filter_data()` for task-specific filtering based on `filter_cfg`; keep the return value as `list[dict]`.
6. Validate with `dataset.metainfo`, `len(dataset)`, `dataset.get_data_info(0)`, and `dataset[0]` before using a dataloader.

### Annotation Format

A standard serialized annotation should load to this shape:

```python
{
    "metainfo": {"classes": ["cat", "dog"]},
    "data_list": [
        {"img_path": "train/a.jpg", "label": 0},
        {"img_path": "train/b.jpg", "label": 1},
    ],
}
```

`BaseDataset.load_data_list()` expects:

- the loaded object is a `dict`;
- both `data_list` and `metainfo` are present;
- each parsed sample is a `dict`, or a `list[dict]` for one raw record that expands into multiple samples.

If any of those checks fails, fix the annotation converter or override `load_data_list()` instead of patching later pipeline steps.

## Metadata and Paths

Metadata priority is, from strongest to weakest:

1. constructor `metainfo=`;
2. class-level `METAINFO`;
3. annotation-file `metainfo`.

Path behavior:

- `ann_file` is joined with `data_root` when it is relative and `data_root` is set.
- each value in `data_prefix` must be a string; relative values are joined with `data_root`.
- default `parse_data_info()` asserts each `data_prefix` key exists in every raw record and joins that prefix to the record value.
- use backend-agnostic `mmengine.fileio.join_path` if you build paths that may later target non-local backends.

Keep source records immutable when possible. Copy records before mutating inside `parse_data_info()` or transforms if the same raw dict can be reused, serialized, cached, or inspected later.

```python
class TinyDataset(BaseDataset):
    METAINFO = {"classes": ("neg", "pos")}

    def parse_data_info(self, raw_data_info):
        data_info = raw_data_info.copy()
        data_info["label"] = int(data_info["label"])
        return data_info
```

## Initialization and Subsets

Important `BaseDataset` constructor options:

| Option | Use | Practical check |
| --- | --- | --- |
| `lazy_init=True` | Defer annotation loading until `full_init()`, `len()`, `get_data_info()`, or `__getitem__()` | Call `full_init()` manually before sending the dataset to dataloader workers to avoid repeated per-worker parsing. |
| `serialize_data=True` | Store records as serialized bytes to reduce worker memory duplication | Use `get_data_info()` for deep-copied records instead of reading internal buffers. |
| `indices=int or sequence` | Keep a subset during initialization | Confirm `sample_idx` in returned records reflects the subset index, not necessarily the original raw order. |
| `test_mode=True` | Evaluation/test behavior | A transform returning `None` is an error instead of triggering training-time refetch. |
| `max_refetch` | Training-time retries when a pipeline returns `None` | If exceeded, inspect file paths and transforms that may reject records too often. |

`get_subset(indices)` returns a copied subset dataset. `get_subset_(indices)` mutates the dataset in place. Use the non-mutating form for debugging or evaluation forks.

## Transform Pipelines

`Compose` accepts either callables or config dicts that build to callables through the transform registry.

Behavior to rely on:

- `Compose(None)` and `Compose([])` are no-op pipelines.
- A non-callable transform or config that builds to a non-callable raises `TypeError`.
- Each transform receives a `dict` and should return a `dict` with the next contract fields.
- If any transform returns `None`, `Compose` returns `None` immediately.
- During training, `BaseDataset.__getitem__()` refetches another sample when the pipeline returns `None`; during test mode, it raises because test data should be deterministic.

Use this pattern for tiny custom transforms:

```python
class AddSummary:
    def __call__(self, data):
        data = data.copy()
        values = data["values"]
        data["inputs"] = sum(values)
        data["data_sample"] = {"label": data["label"], "sample_idx": data["sample_idx"]}
        return data
```

Validation sequence:

1. Apply `dataset.pipeline(dataset.get_data_info(0))` to inspect one transformed sample.
2. Confirm all required keys exist after every transform boundary.
3. Confirm transforms that may drop invalid data return `None` intentionally and rarely.
4. Confirm test/eval pipelines never return `None`.

## Samplers and Collation

When a dataloader is passed to an MMEngine runner as a config dict, prefer an explicit sampler config and avoid mixing PyTorch `shuffle=` with a `sampler`.

Typical dataloader fragment:

```python
train_dataloader = dict(
    batch_size=2,
    dataset=dict(type="TinyDataset", ann_file="train.json", pipeline=[...]),
    sampler=dict(type="DefaultSampler", shuffle=True),
    collate_fn=dict(type="pseudo_collate"),
)
```

`DefaultSampler` works in both distributed and non-distributed settings:

- `shuffle=True` shuffles deterministically from `seed + epoch`.
- `seed=None` lets MMEngine synchronize a seed across ranks.
- `round_up=True` repeats samples so the sample count is evenly divisible by world size.
- call `set_epoch(epoch)` in custom loops when `shuffle=True` and you need a new epoch order.

For iteration-based loops, `InfiniteSampler` yields an infinite rank-sharded stream and does not use `set_epoch()`.

Choose collate behavior deliberately:

| Collate | Behavior | Use when |
| --- | --- | --- |
| `pseudo_collate` | Recurses through mappings/sequences but preserves tensors, arrays, numbers, strings, bytes, and `BaseDataElement` objects as per-sample lists. | Models/data preprocessors expect lists of variable-size items or per-sample data elements. |
| `default_collate` | Recurses and stacks tensors/arrays/numbers when shapes match, but leaves `BaseDataElement`, strings, and bytes unstacked. | Inputs are fixed-shape tensors and downstream code expects a batch tensor. |

Common validation checks:

- For `default_collate`, all tensor/array fields at the same key must have compatible shapes.
- For nested sequences, every item in the batch must have the same length.
- For data samples based on `BaseDataElement`, expect a list of samples after either built-in collate function.

## Dataset Debugging Mini-Checklist

- Annotation loads successfully with `mmengine.fileio.load()` and has `metainfo` plus `data_list`.
- `load_data_list()` returns `list[dict]`, not a generator, mapping, tuple, or list containing non-dicts.
- `parse_data_info()` does not mutate source records unintentionally.
- `metainfo` contains required class/task names after priority merging.
- `dataset.full_init()` succeeds before dataloader worker construction.
- `dataset.get_data_info(0)` includes `sample_idx` and expected joined paths.
- `dataset[0]` returns the model/data-preprocessor contract fields after transforms.
- Collate output matches model expectations: list-preserving versus stacked tensors.
