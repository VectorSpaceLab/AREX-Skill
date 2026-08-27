---
name: pipeline-composition
description: "Build, edit, validate, seed, and debug Albumentations augmentation
  pipelines with Compose and composition combinators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Albumentations Pipeline Composition

Use this sub-skill when an agent needs to assemble or modify an Albumentations pipeline, reason about pipeline-level validation, or debug pipeline randomness and target routing.

## Route Here For

- Building `A.Compose` / `A.ReplayCompose` pipelines around existing transforms.
- Choosing composition blocks: `OneOf`, `SomeOf`, `RandomOrder`, `Sequential`, `OneOrOther`, and `SelectiveChannelTransform`.
- Enabling `strict`, `is_check_shapes`, `additional_targets`, `mask_interpolation`, `seed`, or `save_applied_params` on a pipeline.
- Editing a pipeline with `+`, left-`+`, or `-` while preserving compose configuration.
- Debugging invalid keys, shape mismatches, bad operator operands, seed expectations, label-field routing, or mask interpolation surprises.

## Route Elsewhere

- Transform family choice and transform parameter recipes: `../transform-catalog/`.
- Bbox, keypoint, label, volume, and 3D target formats: `../targets-and-formats/`.
- Replay dictionaries, save/load, JSON/YAML, and reproducibility artifacts: `../serialization-and-reproducibility/`.
- Tensor conversion and dataloader placement: `../framework-integration/`.

## References And Helpers

- `references/composition-api.md`: API signatures, composition semantics, validation options, seed behavior, target routing, operator edits, and worked examples.
- `references/troubleshooting.md`: Symptom-driven fixes for invalid keys, mismatched shapes, single-transform warnings, missing labels, seed confusion, operator failures, and mask interpolation issues.
- `scripts/check_pipeline_contract.py`: A tiny self-contained checker that exercises strict keys, shape checks, additional depth targets, mask interpolation propagation, operator metadata preservation, and seed independence from global NumPy seeding.

## Default Composition Pattern

Prefer an explicit, strict top-level `Compose` while developing, then relax only the checks that are intentionally incompatible with the data:

```python
import albumentations as A

pipeline = A.Compose(
    [
        A.Resize(256, 256, p=1),
        A.OneOf([A.HorizontalFlip(p=1), A.VerticalFlip(p=1)], p=0.5),
    ],
    additional_targets={"depth": "mask"},
    is_check_shapes=True,
    strict=True,
    mask_interpolation=0,
    seed=137,
    save_applied_params=True,
)
result = pipeline(image=image, mask=mask, depth=depth)
```

Keep `Compose` calls keyword-only: use `pipeline(image=image, mask=mask)`, not `pipeline(image)`.
