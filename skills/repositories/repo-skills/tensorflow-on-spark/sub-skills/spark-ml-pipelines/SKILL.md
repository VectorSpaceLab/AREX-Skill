---
name: spark-ml-pipelines
description: "Operate TensorFlowOnSpark Spark ML TFEstimator and TFModel
  DataFrame workflows for training and batch inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Spark ML Pipelines

Use this sub-skill for TensorFlowOnSpark DataFrame workflows built on Spark ML `Estimator` and `Model` APIs.

## Scope

Covers:
- `pipeline.TFEstimator` and `pipeline.TFModel`
- `Namespace`, `TFParams`, and ML param mixins
- `input_mapping` / `output_mapping`
- TF1 vs TF2 SavedModel loading, `tag_set`, `signature_def_key`, and `export_dir`
- batch inference model/session caching on Spark Python workers
- lexicographic mapping rules for DataFrame columns and tensor names

Does not cover:
- raw RDD queue training or `TFNode.DataFeed` loop semantics → [`../datafeed-inputmode/SKILL.md`](../datafeed-inputmode/SKILL.md)
- TFRecord DataFrame load/save and schema conversion → [`../dataframes-tfrecords/SKILL.md`](../dataframes-tfrecords/SKILL.md)
- full example command orchestration and `spark-submit` wiring → [`../examples-conversion/SKILL.md`](../examples-conversion/SKILL.md)

## Start here

- [`references/api-reference.md`](references/api-reference.md) for signatures, ordering rules, and TF1/TF2 behavior
- [`references/pipeline-workflows.md`](references/pipeline-workflows.md) for train/inference recipes and SavedModel selection
- [`references/troubleshooting.md`](references/troubleshooting.md) for common failure modes and recovery steps
- [`scripts/render_pipeline_template.py`](scripts/render_pipeline_template.py) to generate a Python skeleton with mapping placeholders

## Operating rules

1. Treat Spark ML pipeline use as `InputMode.SPARK` only.
2. Keep `input_mapping` and `output_mapping` as plain dictionaries.
3. Remember that training input columns are selected in lexicographic order by DataFrame column name.
4. Remember that inference output columns are ordered by lexicographic output tensor name.
5. Use `export_dir`, `tag_set`, and `signature_def_key` together when loading SavedModels for inference.
6. If a task depends on raw RDD queues, TFRecords, or example command flows, route it to the sibling sub-skill instead of expanding this one.
7. The helper script emits code templates only; it never trains a model or submits Spark jobs.
