---
name: v2-components
description: "Guides Waymo Open Dataset V2 columnar components, Parquet tags,
  dataclass schemas, object assets, and Pandas or Dask dataframe joins."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# V2 Components

Use this sub-skill when the task mentions WOD V2, Perception 2.0, component tags, Parquet component directories, `Component` dataclasses, flattened dictionaries, Arrow schemas, `v2.merge`, Pandas/Dask key joins, or object-asset V2 structures.

Read:

- [references/api-reference.md](references/api-reference.md) for verified signatures, component tags, dataclass rules, and exported helpers.
- [references/workflows.md](references/workflows.md) for component flatten/unflatten, schema, Parquet, and merge recipes.
- [references/troubleshooting.md](references/troubleshooting.md) for key-column mismatches, repeated-field columns, PyArrow/Pandas/Dask issues, and object-asset pitfalls.

Useful bundled check:

- [`scripts/inspect_v2_components.py`](scripts/inspect_v2_components.py) lists installed V2 tags, validates a tiny component schema, and runs a one-row `v2.merge` check.

Route elsewhere:

- Use `dataset-utils` for v1 TFRecord `Frame` parsing, range images, camera projections, maps, or point clouds.
- Use `metrics-evaluation` for detection/tracking/motion metric wrappers and submission scoring.
- Use `camera-and-segmentation` for camera-only challenge, PVPS, semantic segmentation, or Deeplab2 camera-segmentation issues.

Typical flow:

1. Verify the package with the root environment checker or this sub-skill script.
2. Identify component tags with `v2.ALL_TAGS` or `v2.TAG_BY_COMPONENT`.
3. For custom or reconstructed records, use `Component.to_flatten_dict()`, `Component.from_dict()`, and `Component.schema()` rather than inventing column names.
4. Merge component tables with `v2.merge(left, right, left_nullable=..., right_nullable=..., left_group=..., right_group=...)` and check key prefixes before joining.
