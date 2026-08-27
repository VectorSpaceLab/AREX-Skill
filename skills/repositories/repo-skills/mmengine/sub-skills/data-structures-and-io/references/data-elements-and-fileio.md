# Data Elements and File IO

This reference covers MMEngine data containers and backend-agnostic file IO. Use it when code must pass structured samples between datasets, models, visualizers, evaluators, and storage backends.

## BaseDataElement

`BaseDataElement` separates sample metadata from data fields while exposing both as object attributes.

Use `metainfo` for stable contextual facts:

- `img_id`, `img_path`, `ori_shape`, `img_shape`, `scale_factor`, `classes`, task names, and visualization context.
- Values are set at construction with `metainfo={...}` or later with `set_metainfo({...})`.

Use data fields for annotations, predictions, and tensors/arrays that change through the pipeline:

- `gt_instances`, `pred_instances`, `scores`, `labels`, `bboxes`, masks, embeddings, or nested data elements.
- Values are set with keyword arguments, `set_data({...})`, or attribute assignment.

Important rules:

- A field name cannot exist in both metainfo and data; rename one side or delete the old field first.
- `keys()`, `values()`, and `items()` return data fields only.
- `metainfo_keys()`, `metainfo_values()`, and `metainfo_items()` return metadata only.
- `all_keys()` and `all_items()` include both groups.
- `get(key, default)` can read either group.
- `to()`, `cpu()`, `cuda()`, `detach()`, `numpy()`, and `to_tensor()` apply to tensor-like data fields and nested data elements.
- `to_dict()` recursively converts nested data elements to plain dictionaries.

Tiny pattern:

```python
sample = BaseDataElement(
    metainfo={"sample_idx": 0, "img_shape": (32, 32)},
    gt_label=0,
)
assert "sample_idx" in sample.metainfo_keys()
assert "gt_label" in sample.keys()
```

## InstanceData

`InstanceData` is for variable numbers of instance-level annotations or predictions, such as boxes, labels, scores, masks, polygons, or track ids.

Strict contract:

- every data field must implement `__len__`;
- after the first field is set, every new field must have the same length;
- integer indexing keeps an `InstanceData` result with length one;
- slicing, list indices, NumPy indices, long tensors, and bool tensors slice every field consistently;
- bool tensor indices must be 1D and match the instance length;
- `InstanceData.cat([...])` requires all inputs to be `InstanceData` and to have exactly the same data/metainfo keys.

Supported field values include tensors, NumPy arrays, lists, tuples, strings, and custom objects that implement compatible `__len__`, `__getitem__`, and, for concatenation or some bool slicing paths, `cat`.

Debug pattern for length mismatches:

```python
instances = InstanceData(metainfo={"img_shape": (32, 32)})
instances.bboxes = torch.zeros((2, 4))
instances.labels = torch.tensor([0, 1])
# instances.scores = torch.ones(3)  # invalid: length 3 does not match length 2
```

When designing datasets, set all instance fields from the same filtered source list so boxes, labels, scores, masks, and ids stay aligned.

## PixelData

`PixelData` is for pixel-level annotations or predictions, such as segmentation masks, heatmaps, and feature maps.

Strict contract:

- values must be `torch.Tensor` or `numpy.ndarray`;
- values must be 2D or 3D;
- 2D values are expanded to shape `(1, H, W)` with a warning;
- all fields must share the same height and width;
- slicing supports `(height_index, width_index)` using integers or slices and returns another `PixelData`.

Use `pixel_data.shape` to check `(H, W)`. If assigning a new map fails, compare `value.shape[-2:]` with `pixel_data.shape`.

## LabelData

`LabelData` is a lightweight label-level data element. It inherits `BaseDataElement` and adds helpers:

- `LabelData.label_to_onehot(label, num_classes)` converts label-format tensors into one-hot tensors.
- `LabelData.onehot_to_label(onehot)` converts a valid 1D one-hot tensor back to label indices.

Validation points:

- `label_to_onehot` requires all labels to be less than `num_classes`.
- `onehot_to_label` requires a 1D tensor containing values in `[0, 1]`.

## Data Element Batching

Built-in MMEngine collate functions do not stack `BaseDataElement` objects. They preserve samples as lists so a model data preprocessor or task-specific pack transform can handle variable-size targets.

Practical expectations:

- Dataset item: `{"inputs": tensor_or_array, "data_sample": BaseDataElement(...)}`.
- `pseudo_collate`: `inputs` becomes a list of per-sample values; `data_sample` becomes a list of objects.
- `default_collate`: fixed-shape `inputs` becomes a stacked tensor; `data_sample` remains a list of objects.

Route model-side `forward`, `train_step`, `val_step`, evaluator, and metric handling to `../models-metrics-and-inference/SKILL.md`.

## Unified File IO

Prefer `mmengine.fileio` functions for new code. They infer a backend from URI prefixes or explicit `backend_args` and provide one public surface for local files and supported remote backends.

Common helpers:

| Helper | Contract |
| --- | --- |
| `load(file, file_format=None, backend_args=None)` | Load JSON, YAML, or pickle data from a path or file-like object; format is inferred from extension unless specified. |
| `dump(obj, file=None, file_format=None, backend_args=None)` | Dump JSON, YAML, or pickle to a string/file-like object/path. |
| `get(filepath, backend_args=None)` / `put(bytes, filepath, backend_args=None)` | Read/write bytes. |
| `get_text(filepath, encoding="utf-8", backend_args=None)` / `put_text(str, filepath, backend_args=None)` | Read/write text. |
| `exists`, `isfile`, `isdir` | Check backend path state. |
| `join_path` | Join path components with the selected backend semantics. |
| `list_dir_or_file` | Iterate relative entries under a directory, optionally filtering by file/dir, suffix, and recursion. |
| `get_local_path` | Context manager that yields a local path for local or backend-managed files. |
| `copyfile`, `copytree`, `remove`, `rmtree` | Backend-routed file operations; use carefully and avoid destructive calls in smoke scripts. |

Safe local round-trip:

```python
from mmengine import fileio

payload = {"samples": [{"id": 1, "label": "cat"}]}
fileio.dump(payload, "ann.json")
assert fileio.load("ann.json") == payload
fileio.put_text("a\nb\n", "labels.txt")
assert list(fileio.list_dir_or_file(".", list_dir=False, suffix=".txt"))
```

## Backends and Arguments

Backend resolution rules:

- a path without `://` uses the local backend by default;
- URI prefixes such as `http`, `https`, `s3`, and `petrel` select matching registered backends when available;
- `backend_args={"backend": "local"}` or another backend name overrides prefix inference;
- helper functions can reuse singleton backend instances internally for the same prefix and arguments.

Use `backend_args` in new code. `FileClient` and `file_client_args` still exist for compatibility but are documented as deprecated paths; if you encounter them, migrate to unified file IO helpers when changing code.

Optional backend cautions:

- LMDB, Memcached, Petrel, HTTP, or cloud/object storage may require optional packages, credentials, services, or network access.
- Do not assume a remote URI can be listed, copied, or removed unless the backend implements that method.
- Test backend-agnostic code first with local temp directories and explicit `backend_args={"backend": "local"}` if you need to avoid prefix ambiguity.

## File IO Validation Checklist

- Serialized data has a supported extension or passes `file_format` explicitly.
- New code passes `backend_args`, not `file_client_args`.
- Path joins use `fileio.join_path` when the path might not be local.
- Existence/listing code handles relative results from `list_dir_or_file`.
- Optional backend imports and credentials are handled as environment-specific concerns, not hard requirements for local tests.
- Destructive helpers such as `remove` and `rmtree` are scoped to temp/test paths and never run on user data by default.
