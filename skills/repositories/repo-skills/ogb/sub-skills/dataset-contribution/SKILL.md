---
name: dataset-contribution
description: "Routes OGB dataset-export workflows for DatasetSaver and
  OGB-compatible releases."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dataset Contribution

Use this subskill when the task is about packaging a new OGB-compatible dataset
with `DatasetSaver`, generating a `meta_dict.pt`, or validating the layout of a
submission archive.

## Use this subskill when

- The task names `DatasetSaver` or `save_graph_list` / `save_target_labels` /
  `save_split` / `copy_mapping_dir` / `get_meta_dict`.
- The task asks how to prepare `meta_dict.pt`, `mapping/`, or a release zip for
  an external dataset contribution.
- The task needs a tiny end-to-end smoke of the export pipeline.

## First decisions

1. Read [`references/workflows.md`](references/workflows.md) for the step order
   and family constraints.
2. Read [`references/data-formats.md`](references/data-formats.md) for graph,
   split, label, and mapping directory shapes.
3. Read [`references/api-reference.md`](references/api-reference.md) for the
   method order and parameter expectations.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a
   shape, mapping, or zip step fails.
5. If you want a safe end-to-end smoke, run
   [`scripts/datasetsaver-tiny-smoke.py`](scripts/datasetsaver-tiny-smoke.py).

## Main workflow

- Decide whether the dataset is graph-, node-, or link-oriented.
- Build the graph list in the format OGB expects.
- Save labels and splits in the same order that the export helper expects.
- Copy the mapping directory only after the raw and split files are present.
- Generate the `meta_dict.pt` and zip the prepared directory.
- Reload the tiny smoke dataset to confirm the archive structure still works.

## Common routing choices

- Use this subskill for new OGB-compatible releases.
- Use the graph/node/link subskills when the user only needs to consume an
  existing OGB dataset, not package a new one.

## What not to do here

- Do not tell the user to hand-edit the packaged release after the zip step.
- Do not assume heterogeneous `ogbg` export is implemented.
- Do not depend on the original checkout for final runtime guidance.

## Related references

- [`../../references/api-overview.md`](../../references/api-overview.md)
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
