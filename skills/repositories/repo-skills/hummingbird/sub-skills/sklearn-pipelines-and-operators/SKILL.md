---
name: sklearn-pipelines-and-operators
description: "Decide supported sklearn operator, pipeline, data-layout, and
  tree-strategy conversion tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sklearn pipelines and operators

Use this sub-skill when the task is to decide whether a scikit-learn estimator, transformer, or composite pipeline can be converted by Hummingbird, how to keep its input layout valid, or how to choose a tree conversion strategy.

Natural triggers include: supported sklearn operators, `MissingConverter` for a sklearn model, `Pipeline`, `ColumnTransformer`, `FeatureUnion`, pandas DataFrames, multiple inputs, `OneHotEncoder` strings, `tree_implementation`, `tree_op_precision_dtype`, and pipeline conversion parity.

## Route first

- Basic `hummingbird.ml.convert(...)` / `convert_batch(...)` call construction and ordinary CPU parity checks: [`../core-conversion/SKILL.md`](../core-conversion/SKILL.md).
- LightGBM, XGBoost, SparkML, Prophet, or optional source-package dependency questions: [`../optional-source-models/SKILL.md`](../optional-source-models/SKILL.md).
- TorchScript/ONNX/TVM/CUDA backend choice, threading, batching performance, and benchmark work: [`../advanced-backends-and-performance/SKILL.md`](../advanced-backends-and-performance/SKILL.md).

## Use this sub-skill for

1. Checking whether every sklearn operator in a model or pipeline is in a supported family.
2. Understanding parser-level composite wrappers such as `Pipeline`, `ColumnTransformer`, `FeatureUnion`, model-selection wrappers, multi-output wrappers, bagging, and stacking.
3. Choosing the output method family to validate after conversion: `transform`, `predict`, `predict_proba`, `decision_function`, or `score_samples`.
4. Keeping pandas, tuple/multiple-input, column-name, and string-feature layouts aligned between conversion and inference.
5. Selecting and validating tree strategies: `"gemm"`, `"perf_tree_trav"`, or `"tree_trav"`, plus `"float32"`/`"float64"` tree precision.

## Operating path

1. Identify the concrete fitted sklearn classes and any wrappers around them.
2. Check [operator coverage](references/operator-coverage.md). If a wrapper is supported but a child operator is not, the whole pipeline is not convertible without changing that child.
3. For `Pipeline`, `ColumnTransformer`, `FeatureUnion`, pandas, tuple inputs, or strings, use [pipeline and data formats](references/pipeline-data-formats.md) before writing conversion code.
4. For tree models, decide whether to rely on Hummingbird's depth heuristic or set `extra_config` explicitly, then validate the selected inference method on representative data.
5. If conversion or parity fails, use [troubleshooting](references/troubleshooting.md) and route backend-only issues to the sibling backend sub-skills.

## Bundled references

- [Operator coverage](references/operator-coverage.md) lists supported sklearn families, parser-level wrappers, output method families, and tree strategy knobs.
- [Pipeline and data formats](references/pipeline-data-formats.md) covers ColumnTransformer/FeatureUnion behavior, pandas and tuple inputs, names, and string handling.
- [Troubleshooting](references/troubleshooting.md) maps common sklearn operator, pipeline, string, and tree-strategy failures to corrective actions.

No sub-skill-specific scripts are bundled for this area; use the references above and route generic conversion smokes to the core conversion sub-skill.
