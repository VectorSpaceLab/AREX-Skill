---
name: estimator-workflows
description: "Use legacy TensorFlow Estimator DeepCTR workflows for TFRecord or
  Pandas input when tf.estimator is available."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Estimator Workflows

Use this sub-skill when the task is specifically about DeepCTR's legacy TensorFlow Estimator API: large-scale or distributed-style CTR training with `tf.estimator`, `tf.feature_column`, `input_fn_tfrecord`, `input_fn_pandas`, `RunConfig`, and Estimator checkpoint directories.

## Route by Need

- **Can this runtime run Estimators?** Run [`scripts/check_estimator_runtime.py`](scripts/check_estimator_runtime.py). It reports TensorFlow/DeepCTR versions, top-level `tf.estimator` availability, DeepCTR Estimator imports, the native DeepCTR version gate, and optional constructor/input-function checks.
- **Build TFRecord or Pandas inputs**: Use [`references/tfrecord-and-pandas.md`](references/tfrecord-and-pandas.md) for Criteo-style `FixedLenFeature` schemas, matching `tf.feature_column` objects, safe Pandas preprocessing, and expected Estimator outputs.
- **Choose an Estimator constructor or feature-column pattern**: Use [`references/api-reference.md`](references/api-reference.md) for the Estimator model catalog, constructor parameters, runtime/version facts, optimizer defaults, `model_dir`, and `RunConfig` notes.
- **Diagnose failures**: Use [`references/troubleshooting.md`](references/troubleshooting.md) for missing `tf.estimator` in modern TensorFlow/Keras 3 stacks, dtype/schema mismatches, label-key errors, Pandas missing-value handling, distributed-data expectations, and checkpoint cleanup.

## Boundaries

- This sub-skill uses TensorFlow `tf.feature_column` objects directly. For DeepCTR Keras `SparseFeat`, `DenseFeat`, `VarLenSparseFeat`, and `get_feature_names`, route to [`../data-and-feature-columns/SKILL.md`](../data-and-feature-columns/SKILL.md).
- For Keras-style DeepCTR models such as `DeepFM(...)`, `xDeepFM(...)`, `DIN(...)`, `BST(...)`, compile/fit/predict, or Keras serialization, route to [`../keras-model-workflows/SKILL.md`](../keras-model-workflows/SKILL.md).
- For multi-task Keras models such as `MMOE`, `PLE`, `ESMM`, or `SharedBottom`, route to [`../multitask-models/SKILL.md`](../multitask-models/SKILL.md).
- Do not assume Estimators work just because `deepctr` imports. The constructors call top-level `tf.estimator`; modern TensorFlow builds may omit it.

## Minimum Safe Flow

1. Probe the environment before writing training code:

   ```bash
   python sub-skills/estimator-workflows/scripts/check_estimator_runtime.py --construct-estimator
   ```

2. If the probe reports `unsupported`, use a Keras workflow instead or install a TensorFlow release with top-level `tf.estimator` support. Do not keep debugging DeepCTR feature columns until the runtime gate passes.
3. For Criteo-style TFRecord data, match every serialized feature to both a `tf.io.FixedLenFeature` entry and a compatible `tf.feature_column` entry. Sparse IDs should be `int64` and dense values should be `float32`.
4. Create a fresh `model_dir` for each changed model/feature schema. Reusing checkpoints after changing feature names, bucket sizes, embedding dimensions, or task type commonly causes opaque restore errors.
