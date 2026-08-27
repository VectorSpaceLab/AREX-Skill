# Serialization and reproducibility troubleshooting

## `Lambda` is not serializable

Symptoms:

- `A.to_dict` or `A.save` fails with a message saying `Lambda` needs a `name`.
- `A.from_dict` or `A.load` fails because a nonserializable transform was not supplied.

Fix:

```python
import albumentations as A


def brighten(image, **kwargs):
    return image.clip(0, 250) + 5

custom = A.Lambda(name="brighten", image=brighten, p=1.0)
pipeline = A.Compose([custom])
serialized = A.to_dict(pipeline)
loaded = A.from_dict(serialized, nonserializable={"brighten": custom})
```

The mapping key must match the `name` argument, and the mapping value must be the live `A.Lambda` transform object. The same rule applies to `A.load(..., nonserializable={...})`.

## Actual Python lambdas warn in multiprocessing

`A.Lambda(image=lambda image, **kwargs: image, ...)` may warn that lambda expressions are incompatible with multiprocessing. Use named functions or `functools.partial` when a serialized pipeline may be loaded inside workers.

## Missing custom registry or wrong class name

Symptoms:

- `from_dict` raises `KeyError` for `"__class_fullname__"` or for a class name.
- A custom class serialized in one environment cannot be loaded in another.

Fix:

- Import the module defining the custom serializable transform before calling `A.from_dict` or `A.load`, so Albumentations' serialization registry sees it.
- Avoid naming a custom class the same as a built-in transform unless the serialized config uses a module-qualified name.
- For nonserializable transforms, do not rely on the registry; pass the `nonserializable` mapping.

## YAML fails

Symptoms:

- `A.save(..., data_format="yaml")` raises `ValueError: You need to install PyYAML...`.
- `A.load(..., data_format="yaml")` raises a similar `ValueError`.

Fix:

- Install `PyYAML` in the runtime environment, or use `data_format="json"`.
- Ensure the format argument matches the actual content. A YAML file loaded as JSON, or JSON loaded as YAML in an environment without PyYAML, can fail before Albumentations reconstructs the pipeline.

## Replay dictionary misuse

Symptoms:

- `A.ReplayCompose.replay(...)` raises missing-key errors such as missing `"applied"`, `"params"`, or `"__class_fullname__"`.
- Replay output does not match the recorded augmentation.

Fix:

- Pass the replay sub-dictionary, not the entire call result: `A.ReplayCompose.replay(result["replay"], image=image2)`.
- If `ReplayCompose(save_key="aug_record")` was used, read `result["aug_record"]` instead of `result["replay"]`.
- Do not strip nested transform entries, `params`, or `applied` flags from the replay dictionary.
- Use `ReplayCompose` to record replays; `Compose(..., save_applied_params=True)` is for inspection and does not produce a replay-ready tree.

## Shape changed before replay

Symptoms:

- A recorded crop, pad, bbox, or keypoint replay fails on a second image.
- Replayed geometry differs after resizing or changing the image before replay.

Fix:

1. Replay on data with the original shape and target keys to prove the replay dictionary itself is valid.
2. If the original-shape check passes, move deterministic resizing/padding before `ReplayCompose` in both workflows, or record a new replay after the shape-changing step.
3. For bboxes/keypoints, verify the same `bbox_params`, `keypoint_params`, `label_fields`, and coordinate formats are used. Route format issues to `../targets-and-formats/`.
4. Avoid reusing a replay recorded from one target schema on a different schema unless all sampled params remain valid.

## Seeded pipelines still look random

Symptoms:

- Repeated calls to one seeded `Compose` produce different outputs.
- Setting `np.random.seed()` does not make Albumentations deterministic.

Explanation and fix:

- `Compose` owns its own internal NumPy and Python random generators. Global NumPy/Python seeds do not control it.
- A seeded pipeline produces a deterministic sequence, not the same result forever. To restart the sequence, call `pipeline.set_random_seed(seed)` before the call under test.
- To force one sampled augmentation onto another item, use `ReplayCompose` rather than reseeding a normal `Compose`.

## Loaded config differs only by tuple/list types

JSON and YAML may restore tuples as lists. If a dictionary comparison fails only because `(1, 2)` became `[1, 2]`, normalize those structures or use a comparison that ignores tuple/list type differences. Then still validate actual augmented outputs with a fixed seed.

## Hub operations fail

Symptoms:

- `save_pretrained(..., push_to_hub=True)`, `from_pretrained("repo/id")`, or `push_to_hub(...)` fails with import, HTTP, auth, or missing-file errors.

Fix:

- Install `huggingface_hub` or the package extra that provides it before using remote Hub methods.
- Use local `save_pretrained(directory, key="eval")` and `from_pretrained(directory, key="eval")` for offline workflows.
- Use only `key="train"` or `key="eval"` unless `allow_custom_keys=True`.
- Pass `token` for private repositories or uploads; set `local_files_only=True` only when the config is already cached or present locally.
- Remember Hub configs are still Albumentations JSON serialization. Nonserializable `Lambda` transforms and custom class import requirements are not solved by uploading the config.

## Schema-maintainer tooling is not a runtime fix

Albumentations includes maintainer checks for generated schemas and default values. Those checks are useful as evidence that serialized schema defaults matter, but they are not needed for ordinary pipeline save/load workflows. Runtime troubleshooting should focus on `to_dict`, `from_dict`, `save`, `load`, seeds, replay dictionaries, and target shape/schema compatibility.
