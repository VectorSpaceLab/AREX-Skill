---
name: serialization-and-reproducibility
description: "Save, load, replay, inspect, and reproduce Albumentations
  augmentation pipelines with JSON/YAML serialization, ReplayCompose,
  applied-parameter tracking, custom Lambda mappings, deterministic seeds, and
  Hub caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Albumentations serialization and reproducibility

Use this sub-skill when a task involves persisting augmentation pipelines, comparing a loaded pipeline with the original, replaying exact random choices, recording transform parameters, or diagnosing reproducibility surprises.

## Route first

- Build or edit the initial `A.Compose` / `A.ReplayCompose` structure with `../pipeline-composition/` before serializing it.
- Choose transform families and parameter names with `../transform-catalog/` before saving a config.
- Confirm image, mask, bbox, keypoint, volume, and additional-target schemas with `../targets-and-formats/` before replaying across data.
- Handle PyTorch `Dataset` and dataloader-worker reproducibility with `../framework-integration/` after the Albumentations pipeline itself is correct.

## Use the bundled materials

- `references/serialization-api.md`: Use for `A.to_dict`, `A.from_dict`, `A.save`, `A.load`, JSON/YAML buffers/files, schema shape, custom transform mapping, and Hub save/load methods.
- `references/reproducibility.md`: Use for `ReplayCompose`, `ReplayCompose.replay`, `save_applied_params`, `applied_transforms`, `seed`, `set_random_seed`, and exact-output validation checks.
- `references/troubleshooting.md`: Use for nonserializable `Lambda` failures, missing `nonserializable` keys, YAML dependency errors, replay misuse, shape changes before replay, and Hugging Face Hub network/auth limitations.
- `scripts/roundtrip_pipeline.py`: Run a tiny local smoke check that saves and loads a simple pipeline, resets seeds, verifies equal output, and optionally writes JSON or YAML.

## Standard workflow

1. Make the pipeline serializable: prefer built-in transforms; give `A.Lambda` a stable `name`; keep custom callables available in code that loads the config.
2. Round-trip the configuration with `A.to_dict`/`A.from_dict` or `A.save`/`A.load`, then compare `to_dict()` outputs and seeded augmentation outputs on a tiny fixture.
3. For exact reuse of one random draw, capture `result["replay"]` from `A.ReplayCompose` and pass it to `A.ReplayCompose.replay` with data of compatible targets and shapes.
4. For debugging, use `A.Compose(..., save_applied_params=True)` and inspect `result["applied_transforms"]` for transform names and sampled params.
5. Treat Hub methods as optional sharing helpers: local `save_pretrained`/`from_pretrained` use JSON config files; remote push/download requires `huggingface_hub`, network access, and credentials when needed.
