---
name: data-transforms
description: "Operate Snorkel mappers, preprocessors, augmentation transforms,
  and synthetic helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# data-transforms

Use this sub-skill for Snorkel data-point transforms that stay below labeling, slicing, and model-training workflows.

## Route here for

- `Mapper`, `BaseMapper`, `LambdaMapper`, and `lambda_mapper`
- `Preprocessor`, `preprocessor`, and `SpacyPreprocessor`
- `make_spark_mapper` and `make_spark_preprocessor`
- `TransformationFunction`, `transformation_function`, `TFApplier`, and `PandasTFApplier`
- `ApplyOnePolicy`, `ApplyEachPolicy`, `ApplyAllPolicy`, `RandomPolicy`, and `MeanFieldPolicy`
- `generate_simple_label_matrix`
- tiny smoke checks for copy semantics, memoization, `None`-skips, and preserved indices

## Route elsewhere

- Weak supervision label functions, `LabelModel`, and LF appliers: `../labeling/SKILL.md`
- Slice functions and slice-aware modeling: `../slicing/SKILL.md`
- Tensor datasets, collation, and classifiers: `../classification/SKILL.md`

## Read first

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/data_transform_smoke.py)

## Quick decision map

| Need | Use |
| --- | --- |
| Build or chain a data-point mapper/preprocessor | stay here |
| Parse text into a spaCy `Doc` field | stay here |
| Make a mapper/preprocessor work on Spark `Row` objects | stay here |
| Create augmentation TFs or choose a policy | stay here |
| Build LF or SF logic on top of a shared transform | define the transform here, then route to `../labeling/SKILL.md` or `../slicing/SKILL.md` |
| Turn weak labels or transformed tensors into model inputs | route to `../labeling/SKILL.md` or `../classification/SKILL.md` |

## Typical path

1. Identify the smallest transform primitive that solves the task.
2. Decide whether the input is a plain object, a Pandas row, or Spark `Row`.
3. Pick memoization only when repeated examples are expected.
4. Use the smoke script when you need a quick local check.

```bash
python scripts/data_transform_smoke.py
```

The smoke helper runs only tiny in-memory fixtures. It skips optional spaCy or PySpark checks when those extras are unavailable.
