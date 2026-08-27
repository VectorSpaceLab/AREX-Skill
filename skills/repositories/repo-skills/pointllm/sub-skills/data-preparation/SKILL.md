---
name: data-preparation
description: "Prepare and validate PointLLM Objaverse and ModelNet point-cloud
  and instruction data, including NPY schemas, normalization, dataset APIs, and
  safe tiny fixtures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC-SA 4.0
---

# PointLLM data preparation

Use this route when a Researcher must make point-cloud or instruction data
usable by PointLLM, inspect a dataset configuration, or diagnose a data-shape,
annotation, or collation failure. This is a preparation and validation route;
it does not launch training, generate model responses, or call external GPT
evaluators.

## Quick route

1. Identify the workflow: Objaverse instruction data, Objaverse point-only
   inference input, or ModelNet40 classification data.
2. Establish paths using the layouts in [data-formats.md](references/data-formats.md).
   Do not download or extract data from a validation script.
3. Run the bundled, read-only validator before constructing a dataset:

   ```bash
   python scripts/validate_pointcloud_data.py \
     --data-path data/objaverse_data \
     --anno-path data/anno_data/PointLLM_brief_description_660K_filtered.json \
     --pointnum 8192
   ```

   For a small fixture, use its actual row count, for example
   `--pointnum 4 --max-files 10`. Add `--no-require-annotation-files` only
   when checking standalone NPY files.
4. Inspect the API contract in [api-reference.md](references/api-reference.md)
   before changing `pointnum`, `use_color`, conversation filters, or ModelNet
   YAML. Apply the failure guide in [troubleshooting.md](references/troubleshooting.md)
   when a check fails.
5. Hand point-only inputs to the [inference sibling route](../inference-serving/SKILL.md),
   data arguments and loaders to the [training sibling route](../training/SKILL.md),
   and benchmark-specific ModelNet/Objaverse inputs to the
   [evaluation sibling route](../evaluation/SKILL.md). Keep this route focused
   on the data contract they consume.

## Primary APIs

The route covers `ObjectPointCloudDataset`, `ModelNet`, `pc_norm`,
`pc_normalize`, `farthest_point_sample`,
`DataCollatorForPointTextDataset`, `load_objaverse_point_cloud`, and
`make_object_point_data_module`. Read [api-reference.md](references/api-reference.md)
for signatures and return shapes.

## Required Objaverse contract

- Each colored file is `<object_id>_<pointnum>.npy`; the released training
  convention is `8192` rows and six columns `(xyzrgb)`.
- Columns `0:3` are floating-point coordinates. Columns `3:6` are RGB values
  in the inclusive range `[0, 1]`, not 0--255 bytes.
- Values must be finite. Validate every annotation `object_id` against the
  corresponding file before using a dataset. A missing object file is a data
  error, not a reason to fabricate a zero cloud.
- An annotation is normally a JSON list of records containing `object_id`, an
  optional `conversation_type`, and `conversations`: alternating message
  objects with `from` (`human` or `gpt`) and `value` strings. The first user
  value conventionally contains `<point>`.
- Training data is under `data/anno_data`; the filtered 660K brief file omits
  the reserved validation objects. Complex 70K data uses richer conversation
  types. Evaluation ground truth uses the same object-id/conversation family.

## Required ModelNet contract

- `ModelNet40.yaml` defaults to `DATA_PATH: data/modelnet40_data`, 40 classes,
  `npoints: 8192`, random sampling, and no normals, height, or color.
- The loader expects a pickle `.dat` pair named
  `modelnet40_<train|test>_8192pts_fps.dat`, containing
  `(list_of_points, list_of_labels)`. The test artifact is the primary
  evaluation input; do not substitute Objaverse JSON for it.
- The bundled 40-label order is authoritative for `label_names`; preserve it
  when editing or replacing the YAML/category file.

## Safety gates

- Validate a tiny synthetic NPY/JSON fixture first. Never use a huge download to
  debug a schema or tokenizer issue.
- Keep `pointnum` consistent across filename, loader argument, and model
  expectation. A custom count is possible, but it is not the released
  8192-point convention.
- Treat normalization as a geometry transform: center XYZ at its centroid and
  scale by the maximum Euclidean radius. RGB/other columns are preserved by
  `pc_norm`; `pc_normalize` accepts XYZ only.
- A constant XYZ cloud has zero radius and causes division by zero in the
  repository implementation. Reject it during validation rather than allowing
  NaN/Inf into a model.
- `use_color=False` drops NPY columns after loading. `use_color=True` keeps RGB
  and filters two known corrupted colored Objaverse IDs in the dataset class.
  Do not silently convert arbitrary color ranges.

For exact signatures, filtering order, sampling behavior, and collator shape
rules, read the two bundled references rather than guessing from this router.
