---
name: labeling
description: "Operate Snorkel labeling functions, appliers, LF analysis, and label models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Labeling

Use this sub-skill for Snorkel weak-supervision labeling work:

- authoring `LabelingFunction` objects and `labeling_function` decorators
- attaching small `resources` dictionaries and local `pre` preprocessors to LFs
- applying LFs to lists, NumPy arrays, Pandas DataFrames, Dask DataFrames, and Spark RDDs
- inspecting label matrices with `LFAnalysis`
- training and scoring `LabelModel`
- using `RandomVoter`, `MajorityClassVoter`, and `MajorityLabelVoter`
- filtering training rows with `filter_unlabeled_dataframe`
- using spaCy-based `NLPLabelingFunction` and `spark_nlp_labeling_function`

Do **not** use this sub-skill for:

- generic mapper / preprocessor / transformation mechanics → [`../data-transforms/SKILL.md`](../data-transforms/SKILL.md)
- downstream task, trainer, or classifier work → [`../classification/SKILL.md`](../classification/SKILL.md)
- slicing functions or slice-aware models → [`../slicing/SKILL.md`](../slicing/SKILL.md)

## Fast workflow

1. Define each LF and keep names unique.
2. Add only lightweight local preprocessors and resources that belong to the LF.
3. Apply the LFs with the right applier for the input shape.
4. Run `LFAnalysis` before training any label model.
5. Fit `LabelModel` only after the matrix has meaningful coverage and at least 3 LFs.
6. Use `predict_proba`, `predict`, or a voter baseline to generate weak labels.
7. Filter out unlabeled rows before handing probabilities to a downstream classifier.

## Common routing rules

- Need a reusable data mapper or preprocessor pipeline? Use `data-transforms`.
- Need `Task`, `Trainer`, or weak-label-to-discriminative-model training? Use `classification`.
- Need slice functions or `SliceAwareClassifier`? Use `slicing`.
- Need Dask, spaCy, or Spark setup troubleshooting? See [`references/troubleshooting.md`](references/troubleshooting.md).

## Runtime aids

- API details: [`references/api-reference.md`](references/api-reference.md)
- End-to-end recipes: [`references/workflows.md`](references/workflows.md)
- Troubleshooting guide: [`references/troubleshooting.md`](references/troubleshooting.md)
- CPU smoke check: [`scripts/labeling_smoke.py`](scripts/labeling_smoke.py)
- Optional local Spark smoke: [`scripts/labeling_spark_smoke.py`](scripts/labeling_spark_smoke.py)

## Operational hints

- LFs should return integer labels and use `-1` only for abstain.
- `fault_tolerant=True` on an applier turns LF failures into abstains and records fault counts in metadata.
- `LabelModel` needs a label matrix with at least 3 LFs and labels in `[-1, 0, ..., cardinality-1]`.
- spaCy NLP helpers default to `en_core_web_sm` and memoization is enabled by default for `NLPLabelingFunction`.
- Local Spark use is optional; the Spark smoke script is only for environments with Java and PySpark.
