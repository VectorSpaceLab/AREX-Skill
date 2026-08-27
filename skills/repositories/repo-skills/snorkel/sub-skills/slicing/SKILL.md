---
name: slicing
description: "Operate Snorkel slicing functions, slice monitoring, and
  slice-aware classifiers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Slicing

Use this skill for Snorkel slice functions, slice monitoring, and slice-aware models.

## Use this skill when
- creating `SlicingFunction` objects or `@slicing_function` decorators
- creating `NLPSlicingFunction` or `@nlp_slicing_function` when slice logic depends on spaCy docs
- applying `SFApplier`, `PandasSFApplier`, `DaskSFApplier`, `PandasParallelSFApplier`, or `SparkSFApplier`
- filtering a DataFrame with `slice_dataframe`
- adding slice labels with `add_slice_labels`
- converting a base task into slice tasks with `convert_to_slice_tasks`
- building or scoring `SliceAwareClassifier` and `SliceCombinerModule`

## Route other work elsewhere
- Generic transforms or spaCy preprocessing mechanics -> `../data-transforms/SKILL.md`
- `DictDataset`, `DictDataLoader`, `Task`, `Trainer`, or tensor-shape issues -> `../classification/SKILL.md`
- Weak-supervision LFs, `LFApplier`, or `LabelModel` -> `../labeling/SKILL.md`

## Start with
- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/slicing_smoke.py)

## Operating notes
- Slice memberships should be binary masks; use truthy in-slice values.
- `SFApplier` and `PandasSFApplier` return named-field recarrays.
- `make_slice_dataloader` needs the base task labels already in the dataset.
- `score_slices` evaluates `pred` labels on the base task and skips `ind` labels.
- `SliceAwareClassifier` and `SliceCombinerModule` are binary-only.
- Optional backends live under `snorkel.slicing.apply.dask` and `snorkel.slicing.apply.spark`; see troubleshooting if Dask, PySpark, Java, or spaCy are missing.
