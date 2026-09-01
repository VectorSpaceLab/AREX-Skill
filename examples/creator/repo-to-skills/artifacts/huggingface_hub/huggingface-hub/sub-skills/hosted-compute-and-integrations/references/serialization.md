# Serialization: DDUF and torch checkpoints

Read this reference for local DDUF archives, safetensors/pickle checkpoints,
state-dict sharding, index validation, and local round trips. These operations
write files but do not contact the Hub by themselves. Uploading the outputs,
loading a remote id, or publishing a mixin model is a separate credentialed
network operation.

## Public serialization surface

Representative checked public exports are:

```python
from huggingface_hub import (
    DDUFEntry,
    export_entries_as_dduf,
    export_folder_as_dduf,
    get_torch_storage_id,
    get_torch_storage_size,
    load_state_dict_from_file,
    load_torch_model,
    read_dduf_file,
    save_torch_model,
    save_torch_state_dict,
    split_state_dict_into_shards_factory,
    split_torch_state_dict_into_shards,
)
```

`StateDictSplit` and the torch helpers are also available from
`huggingface_hub.serialization`. Use top-level public imports for the DDUF
helpers. Do not import private `_dduf`, `_torch`, or `_base` functions into
application code.

## Torch save, split, and load

`save_torch_model(model, save_directory, *, filename_pattern=None,
force_contiguous=True, max_shard_size="5GB", metadata=None,
safe_serialization=True, is_main_process=True,
shared_tensors_to_discard=None)` gets `model.state_dict()` and delegates to
`save_torch_state_dict` with the same options.

`save_torch_state_dict(state_dict, save_directory, *, filename_pattern=None,
force_contiguous=True, max_shard_size="5GB", metadata=None,
safe_serialization=True, is_main_process=True,
shared_tensors_to_discard=None)` writes one or more checkpoint files. The target
directory must already exist. Defaults are safetensors with a
`model{suffix}.safetensors` pattern. A sharded save additionally writes
`model.safetensors.index.json` with:

```json
{
  "metadata": {"total_size": 1234},
  "weight_map": {
    "layer.weight": "model-00001-of-00002.safetensors"
  }
}
```

`max_shard_size` can be bytes or a string with `KB`, `MB`, `GB`, or `TB`.
Sharding follows state-dict iteration order; it does not optimize bin packing.
A single tensor larger than the limit remains alone in a shard larger than the
limit. The saver removes old files matching the chosen pattern when
`is_main_process=True`; use only one main process for cleanup/index writes in a
distributed job.

Safe serialization needs `safetensors`. Shared tensor storage cannot be fully
represented; the helper selects one name and records discarded names in
metadata unless `shared_tensors_to_discard` is supplied. For a Transformers
model, pass its tied-weight names. `force_contiguous=True` makes tensors
compatible with safetensors but can change memory layout/performance. Inspect
metadata and round-trip values rather than assuming storage aliasing survived.

Inspect a split without writing:

```python
split = split_torch_state_dict_into_shards(
    state_dict,
    filename_pattern="model{suffix}.safetensors",
    max_shard_size="1KB",
)
assert set(split.tensor_to_filename) == set(state_dict)
assert sum(len(v) for v in split.filename_to_tensors.values()) == len(state_dict)
```

The generic `split_state_dict_into_shards_factory` requires a storage-size
function, a filename pattern containing `{suffix}`, an optional storage-id
function, and a maximum size. Use it only to integrate another tensor type; for
torch, prefer the dedicated helper.

Load with:

```python
result = load_torch_model(
    model,
    checkpoint_path,
    strict=True,
    safe=True,
    map_location="cpu",
)
assert result.missing_keys == []
assert result.unexpected_keys == []
```

`checkpoint_path` may be one checkpoint file or a directory with a generated
index/single model file. `safe=True` looks for safetensors. Set `safe=False`
only when intentionally allowing fallback to pickle, and never for an
untrusted source. `filename_pattern` takes precedence over `safe` when supplied.
`strict=False` reports missing/unexpected keys; `strict=True` fails fast for a
mismatch. `map_location`, `weights_only`, and `mmap` control torch loading, with
version-dependent support.

`load_state_dict_from_file(path, map_location=None, weights_only=False,
mmap=False)` auto-detects `.safetensors`; other files use `torch.load`. A
safetensors file should have metadata format `pt` or `mlx` when metadata is
present. A missing file raises `FileNotFoundError`; an invalid checkpoint
folder or incompatible format raises `ValueError`/`OSError`.

### Index safety

The sharded loader validates every filename from `weight_map` before loading:
absolute paths, Windows drives/UNC roots, any `..` component, and an extension
that does not match the index format are rejected. Do not edit generated index
files by string substitution. If consuming an external index, independently
assert:

- top-level `weight_map` is a mapping of expected tensor keys to strings;
- every shard name is relative, basename-like, and has the expected extension;
- every referenced shard exists under the checkpoint directory;
- no extra shard format is silently enabled; and
- strict model keys match before trusting the restored model.

## DDUF

DDUF is an early diffusion-model archive based on an uncompressed ZIP layout.
It is not a general bundle or an arbitrary directory tree. Export signatures
are:

```python
export_entries_as_dduf(dduf_path, entries) -> None
export_folder_as_dduf(dduf_path, folder_path) -> None
read_dduf_file(dduf_path) -> dict[str, DDUFEntry]
```

Each entry is `(archive_name, path_or_bytes)`. Content can be a local path
string, `Path`, or bytes. Valid extensions are currently `.json`, `.model`,
`.safetensors`, and `.txt`. Names use `/`, not `\`, and support at most one
directory level. Entry names must be unique. `model_index.json` is mandatory,
must parse to a dictionary, and must name every folder represented in the
archive. Every represented folder must contain at least one of
`config.json`, `tokenizer_config.json`, `preprocessor_config.json`, or
`scheduler_config.json`.

A tiny local archive can carry safetensors bytes:

```python
import json
import safetensors.torch
from huggingface_hub import export_entries_as_dduf, read_dduf_file

weights = safetensors.torch.save(state_dict)
export_entries_as_dduf(
    "tiny.dduf",
    [
        ("model_index.json", json.dumps({"_class_name": "Tiny"}).encode()),
        ("model.safetensors", weights),
    ],
)
entries = read_dduf_file("tiny.dduf")
with entries["model.safetensors"].as_mmap() as mm:
    restored = safetensors.torch.load(mm)
```

`export_folder_as_dduf` recursively scans a folder but includes only allowed
extensions and skips files deeper than one directory. It therefore may silently
omit unrelated files or over-nested components; compare the returned archive
entry set with the expected model index after export.

`read_dduf_file` reads metadata and returns `DDUFEntry` objects containing
filename, byte offset, and length. `read_text()` is for JSON/text; `as_mmap()`
allows zero-copy-style bytes for safetensors loading. The archive must be
uncompressed. Corruption, a missing index, bad structure, or invalid entry name
raises a DDUF-specific error.

### DDUF path safety

The current parser intentionally performs limited validation and does not
extract entries. Never pass an entry name directly to filesystem extraction or
join it under a destination without an independent safe-relative-path check.
Reject absolute paths, drive/root components, empty components, `.`/`..`, NULs,
backslashes, over-nesting, and unexpected extensions before writing an entry or
materializing it. Prefer reading through `DDUFEntry` instead of unzipping.

Differentiate errors:

- `DDUFInvalidEntryNameError`: direct entry-name validation failure;
- `DDUFExportError`: export wrapper for invalid/duplicate names, malformed or
  missing `model_index.json`, bad content type, or inconsistent structure;
- `DDUFCorruptedFileError`: a read archive is compressed, malformed, missing
  required index/config, or otherwise inconsistent.

Delete a partially-written output before retrying an export. Correct the index
and entry names in memory, then recreate the archive atomically in a temporary
directory rather than appending to a failed file.

## Local integrated verification

Use [`../scripts/local_integration_smoke.py`](../scripts/local_integration_smoke.py)
to exercise a tiny PyTorch mixin model, generated card, sharded safetensors,
DDUF archive, and mocked configuration recovery. The script asserts that no
network socket is opened and no Hub token is needed. Native serialization,
DDUF, mixin, and card tests validate individual pieces; the integrated fixture
adds cross-format metadata/config consistency and no-remote-mutation assertions.
