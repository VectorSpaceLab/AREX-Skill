# Serialization API

Albumentations 2.0.8 exposes serialization functions at the package top level. They preserve pipeline configuration, not the sampled random state of a previously executed call. Use `seed`, `set_random_seed`, or `ReplayCompose` when output reproducibility is required.

## Public functions

| API | Signature summary | Use |
| --- | --- | --- |
| `A.to_dict(transform, on_not_implemented_error="raise")` | `transform` must implement Albumentations serialization; `on_not_implemented_error` is `"raise"` or `"warn"` | Convert a transform or compose pipeline into plain Python data with `"__version__"` and `"transform"` keys. |
| `A.from_dict(transform_dict, nonserializable=None)` | `nonserializable` maps names to live nonserializable transform objects | Reconstruct a transform or pipeline from a `to_dict`-style dictionary. |
| `A.save(transform, filepath_or_buffer, data_format="json", on_not_implemented_error="raise")` | `filepath_or_buffer` can be a string path, `Path`, or text buffer; `data_format` is `"json"` or `"yaml"` | Write serialized config to disk or a text buffer. |
| `A.load(filepath_or_buffer, data_format="json", nonserializable=None)` | Reads a path or text buffer; accepts the same `nonserializable` mapping as `from_dict` | Load a config and reconstruct the pipeline. |

## Serialization shape

A simple pipeline serializes as a dictionary like:

```python
{
    "__version__": "2.0.8",
    "transform": {
        "__class_fullname__": "Compose",
        "p": 1.0,
        "transforms": [{"__class_fullname__": "HorizontalFlip", "p": 0.5}],
        "bbox_params": None,
        "keypoint_params": None,
        "additional_targets": {},
        "is_check_shapes": True,
        "seed": None,
    },
}
```

`from_dict` resolves registered transform names. For Albumentations classes, short names such as `"HorizontalFlip"` are used. Custom serializable classes may need their full module-qualified name if it overlaps a built-in name.

## JSON and YAML

```python
import io
import albumentations as A

transform = A.Compose([A.Resize(128, 128), A.HorizontalFlip(p=0.5)], seed=137)

buffer = io.StringIO()
A.save(transform, buffer, data_format="json")
buffer.seek(0)
loaded = A.load(buffer, data_format="json")
```

For YAML, use `data_format="yaml"`. Saving or loading YAML requires `PyYAML`; if it is unavailable Albumentations raises a `ValueError` telling you to install it. JSON has no extra package expectation.

## Validation after load

Prefer these checks after writing or loading a production pipeline:

```python
import numpy as np

seed = 137
image = np.zeros((32, 32, 3), dtype=np.uint8)
original = A.Compose([A.RandomCrop(16, 16), A.HorizontalFlip(p=0.5)])
loaded = A.from_dict(A.to_dict(original))

original.set_random_seed(seed)
loaded.set_random_seed(seed)
assert original.to_dict()["transform"] == loaded.to_dict()["transform"]
np.testing.assert_array_equal(original(image=image)["image"], loaded(image=image)["image"])
```

When comparing dictionaries, remember that JSON/YAML may round-trip tuples as lists. For strict tests, compare meaningful configuration fields or normalize tuple/list differences.

## Nonserializable transforms

`A.Lambda` is deliberately nonserializable because it stores Python callables. To serialize its position in a pipeline, provide a stable `name`. To load the config, pass a `nonserializable` mapping whose key is that name and whose value is the live transform object.

```python
import albumentations as A


def invert_image(image, **kwargs):
    return 255 - image

custom = A.Lambda(name="invert", image=invert_image, p=1.0)
pipeline = A.Compose([A.HorizontalFlip(p=1.0), custom])
serialized = A.to_dict(pipeline)
restored = A.from_dict(serialized, nonserializable={"invert": custom})
```

Rules that matter:

- `A.Lambda(name=None, ...)` cannot be serialized; `to_dict` raises a `ValueError` asking for `name`.
- The mapping key must exactly match the `name` stored in the serialized config.
- The mapping value should be the already-constructed transform, not just the callable.
- Actual Python lambda expressions emit a multiprocessing compatibility warning; use named functions or `functools.partial` when a pipeline will be used in worker processes.

## `on_not_implemented_error`

`A.to_dict` and `A.save` accept `on_not_implemented_error`:

- `"raise"` is safest and fails if a transform cannot preserve its arguments.
- `"warn"` suppresses `NotImplementedError` and serializes an empty transform dictionary for the problematic object; use only for exploratory diagnostics because arguments may not be preserved.

## Backward compatibility behavior

When loading old serialized configs where a non-composition transform lacks `p`, `A.from_dict` inspects that transform constructor and fills its default probability. It emits a warning such as `Transform Resize has no 'p' parameter ... defaulting to 1.0`. Explicit `p` values do not warn. `Compose` without `p` is handled without that warning.

## Hub mixin methods

`A.Compose` and compatible compose classes include Hub-style helpers through the Hub mixin:

- `transform.save_pretrained(save_directory, key="eval", allow_custom_keys=False, repo_id=None, push_to_hub=False, **push_to_hub_kwargs)` writes `albumentations_config_<key>.json` locally and optionally pushes it.
- `A.Compose.from_pretrained(directory_or_repo_id, key="eval", force_download=False, proxies=None, token=None, cache_dir=None, local_files_only=False, revision=None)` loads from a local directory containing the config file, or downloads from the Hub.
- `transform.push_to_hub(repo_id, key="eval", allow_custom_keys=False, commit_message="Push transform using huggingface_hub.", private=False, token=None, branch=None, create_pr=None)` creates or reuses a Hub repo and uploads one config file.

`key` defaults to `"eval"`; accepted keys are `"train"` and `"eval"` unless `allow_custom_keys=True`. Remote operations require the optional `huggingface_hub` package, network access, and a valid token for private or write operations. Local `save_pretrained` still uses Albumentations JSON serialization, so nonserializable transform caveats still apply.
