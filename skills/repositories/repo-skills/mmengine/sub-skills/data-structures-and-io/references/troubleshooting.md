# Troubleshooting Data Structures and IO

Use this reference to diagnose MMEngine dataset, transform, collate, data element, and file backend failures.

## Dataset Loading Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Annotation load raises `TypeError` expecting a dict | Serialized annotation is a list/string or custom format | Convert it to a mapping with `metainfo` and `data_list`, or override `load_data_list()` to return `list[dict]`. |
| Annotation load raises `ValueError` about `data_list` and `metainfo` | Standard `BaseDataset` loader is being used with missing top-level keys | Add both keys even when `metainfo` is empty, or implement a custom loader. |
| `parse_data_info` type error | It returns a non-dict, or a list containing non-dict items | Return one sample as `dict` or multiple samples as `list[dict]`. |
| Prefix-key assertion in `parse_data_info` | `data_prefix` contains a key not present in raw records | Align `data_prefix` keys with raw data fields, or override `parse_data_info()` for custom joining. |
| Missing class/task metadata | Metadata is only in the annotation file but the dataset is lazy and not initialized, or metadata was overridden | Check metadata priority: constructor `metainfo` > class `METAINFO` > annotation `metainfo`; call `full_init()` if annotation metadata is needed. |
| `len(dataset)` or `dataset[0]` unexpectedly triggers loading | Dataset was constructed with `lazy_init=True` | Call `full_init()` deliberately before dataloader worker creation and before timing memory/performance. |
| Large worker memory or repeated parsing | Lazy dataset was handed to a dataloader before full init | Run `dataset.full_init()` in the main process; keep `serialize_data=True` unless debugging raw records. |

## Transform and Pipeline Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Compose` raises `TypeError` for a transform | Transform entry is neither callable nor a config dict that builds to a callable | Pass a callable object/function, or register/build a transform correctly through the transform registry. |
| Training loops refetch many samples | A transform returns `None` frequently | Inspect the first transform returning `None`; validate file paths, random crop/augmentation constraints, and `max_refetch`. |
| Test/eval dataset raises because pipeline returned `None` | Test-mode pipelines cannot drop samples | Make validation/test transforms deterministic and total over every record, or pre-filter invalid records in `filter_data()`. |
| Source annotations change after transform/debugging | `parse_data_info()` or a transform mutates a reused dict in place | Copy the record before modifying fields, especially when records are serialized, cached, or reused in assertions. |
| Later transform misses a key | Earlier transform did not document or return the expected field | Write a stepwise pipeline check that prints or asserts keys after each transform on one sample. |

## Sampler and Collate Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Runner dataloader config rejects or misuses `shuffle` | Dataloader dicts should use an explicit sampler instead of PyTorch-style `shuffle` | Use `sampler=dict(type="DefaultSampler", shuffle=True/False)` and remove dataloader-level `shuffle`. |
| Distributed/non-distributed sample counts differ | `DefaultSampler(round_up=True)` pads to make samples divisible by world size | Set `round_up=False` if exact per-epoch sample count matters, and document evaluation implications. |
| Repeated epoch order with a custom loop | Sampler epoch was not advanced | Call `sampler.set_epoch(epoch)` for `DefaultSampler` when `shuffle=True`. |
| `default_collate` raises shape/type mismatch | Tensor/array fields at the same key have incompatible shapes, or nested sequences have unequal lengths | Use `pseudo_collate` for variable-size data, or pad/resize/normalize shapes before `default_collate`. |
| Model receives list where it expected a tensor | MMEngine default collate for runner configs is often `pseudo_collate` | Set `collate_fn=dict(type="default_collate")` for fixed-shape tensor batches, or update the model/data preprocessor to accept lists. |
| Data sample objects are not stacked | Built-in collate functions preserve `BaseDataElement` objects as lists | Handle data samples in the data preprocessor/model as a list of per-sample containers. |

## Data Element Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Cannot set ... because ... already a metainfo/data field` | Same key is being used for both metainfo and data | Rename fields or delete/pop the old field before setting it in the other group. |
| `InstanceData` length assertion | New field length differs from existing instance fields | Rebuild all fields from the same filtered instance list; compare `len(value)` for every key before assignment. |
| `InstanceData` bool index assertion | Bool mask length does not equal instance count or mask is not 1D | Create the mask from an existing field with length `len(instances)` and keep it 1D. |
| `InstanceData.cat` key assertion | Inputs have different data/metainfo keys | Normalize fields before concatenation; add missing empty fields or concatenate only homogeneous groups. |
| `InstanceData.cat` custom field error | Custom field type lacks compatible `cat` | Store lists/tensors/arrays, or implement a `cat(list_of_values)` method on the custom object. |
| `PixelData` type assertion | Assigned value is not a `torch.Tensor` or `numpy.ndarray` | Convert lists/images to tensors or arrays before assignment. |
| `PixelData` dimension assertion | Value is not 2D or 3D | Keep pixel maps as `(H, W)` or `(C, H, W)`; remove batch dimensions before storing. |
| `PixelData` H/W mismatch | New map has different `shape[-2:]` than existing fields | Resize/pad/crop maps before assignment or store them in separate `PixelData` objects. |
| `LabelData.onehot_to_label` fails | Input is not a 1D one-hot tensor with values in `[0, 1]` | Validate dimensionality and values; use `label_to_onehot` to build canonical one-hot labels. |

## File IO and Backend Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `load` cannot infer format | Path lacks a supported extension or uses a file-like object | Pass `file_format="json"`, `"yaml"`, `"yml"`, `"pickle"`, or `"pkl"`. |
| Backend selected incorrectly | URI prefix and `backend_args` disagree | Remember explicit `backend_args["backend"]` has priority; remove it if prefix inference is desired. |
| Warnings about `FileClient` or `file_client_args` | Legacy compatibility path is being used | Migrate touched code to `mmengine.fileio` helpers with `backend_args`. |
| Unsupported URI/backend | Prefix is not registered or optional backend is unavailable | Use local paths for tests, install/configure the optional backend, or register a backend deliberately. |
| LMDB backend import failure | Optional LMDB dependency is not installed | Treat LMDB as optional; skip or guard backend-specific tests when dependency is missing. |
| HTTP/object-store operation missing | Backend does not implement the requested method | Use only methods supported by that backend, or materialize through `get_local_path()` when appropriate. |
| Directory listing paths look incomplete | `list_dir_or_file` yields paths relative to the listed directory | Join returned names with the root path if absolute paths are needed. |
| Unsafe path assumptions | Code concatenates strings or calls local-only `os.path` logic on remote URIs | Use `fileio.join_path`, `exists`, `isfile`, `isdir`, `get`, `put`, `get_text`, and `put_text` with `backend_args`. |

## Triage Order

1. Reproduce with a tiny local temp directory and no network/backend credentials.
2. Validate annotation loading with `mmengine.fileio.load()` and one `BaseDataset` instance.
3. Inspect `dataset.metainfo`, `len(dataset)`, `dataset.get_data_info(0)`, and `dataset[0]` in that order.
4. Collate two samples manually with the intended collate function.
5. Validate every `InstanceData`/`PixelData` assignment before handing samples to the model.
6. Only after local behavior is correct, enable non-local `backend_args` or runner integration.

Route runner placement and loop-side dataloader construction issues to `../runner-and-training/SKILL.md`. Route model, preprocessor, metric, and evaluator sample expectations to `../models-metrics-and-inference/SKILL.md`.
