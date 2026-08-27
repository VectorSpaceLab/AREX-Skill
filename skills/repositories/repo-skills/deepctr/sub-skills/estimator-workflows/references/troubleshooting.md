# Estimator Troubleshooting

Use this reference when DeepCTR Estimator imports, input functions, TFRecord schemas, Pandas inputs, or checkpointed training fail.

## First probe

Run the bundled probe from the generated skill tree:

```bash
python sub-skills/estimator-workflows/scripts/check_estimator_runtime.py --construct-estimator
```

Interpretation:

- `status: supported` means the local TensorFlow/DeepCTR stack exposes the core Estimator symbols and can import DeepCTR Estimator APIs. If `--construct-estimator` passes too, a tiny `DeepFMEstimator` constructor worked.
- `status: unsupported` means do not debug data or feature columns yet; the runtime lacks a required Estimator surface.
- `native_test_gate: false` means DeepCTR's own Estimator tests would normally skip for that TensorFlow version, even if some imports appear available.

## `DeepFMEstimator` imports but `tf.estimator` is absent

Symptom examples:

```text
AttributeError: module 'tensorflow' has no attribute 'estimator'
AttributeError: module 'tensorflow._api.v2.compat.v1' has no attribute 'estimator'
```

Why it happens:

- DeepCTR Estimator modules may import, but constructors call top-level `tf.estimator.Estimator`, `tf.estimator.ModeKeys`, `tf.estimator.EstimatorSpec`, and `tf.estimator.export.PredictOutput`.
- Some modern TensorFlow/Keras 3 environments removed or no longer expose the legacy Estimator API.
- DeepCTR is installed separately from TensorFlow and cannot add Estimator support if the selected TensorFlow build omits it.

Actions:

1. Run the probe and capture its JSON/text output.
2. If `tf_estimator_available` is false, switch to Keras-style DeepCTR models or use an environment with a TensorFlow release that exposes `tf.estimator`.
3. Do not attempt to fix this by importing `tensorflow.python.*` modules in user code. Those are private APIs and do not restore a coherent Estimator runtime.
4. If TensorFlow 2.x is otherwise required for the project, prefer Keras DeepCTR workflows.

## TensorFlow version gate confusion

DeepCTR's native Estimator tests are gated to TensorFlow versions `<2.0.0` or `>=2.2.0,<2.6.0`. The package advertises TensorFlow 1.15/2.x compatibility overall, but that does not guarantee every Estimator path works on every modern TensorFlow release.

Actions:

- Treat `tf.estimator` availability as the hard runtime requirement.
- Treat the DeepCTR native gate as a confidence signal: if false, run a small constructor/train smoke before launching a real job.
- If the environment uses `TF_USE_LEGACY_KERAS`, verify that TensorFlow and Keras imports still expose `tf.estimator`; legacy Keras does not automatically imply Estimator support.

## TFRecord dtype or shape mismatch

Symptom examples:

```text
Key: C1. Data types don't match. Data type: float but expected type: int64
Cannot reshape a tensor with ... elements to shape [?,1]
Feature ... is required but could not be found
InvalidArgumentError: Name: <unknown>, Feature: I1, Index: 0. Number of float values != expected
```

Common causes:

- Serialized sparse IDs as floats but schema says `tf.int64`.
- Used `categorical_column_with_identity` for a string feature.
- Dense vector stored with shape `(dim,)` but `numeric_column` used scalar shape, or the reverse.
- Label schema shape/dtype does not match DeepCTR head reshape to `[-1, 1]`.
- Feature name typo between writer, `feature_description`, and feature columns.

Actions:

1. Check one serialized example with the exact `feature_description` before training.
2. Match sparse identity columns to `tf.io.FixedLenFeature(shape=(1,), dtype=tf.int64)`.
3. Match dense scalars to `tf.io.FixedLenFeature(shape=(1,), dtype=tf.float32)` and `tf.feature_column.numeric_column(name, shape=(1,))`.
4. Match dense vectors to identical vector shapes in both schema and `numeric_column`.
5. For raw strings, use `categorical_column_with_hash_bucket(..., dtype=tf.string)` or an appropriate vocabulary column, not identity.
6. Rebuild TFRecords after changing encoding or schema; do not reuse old files with new feature columns.

## Label key wrong or unavailable

Symptom examples:

```text
KeyError: 'label'
Feature label is required but could not be found
Estimator.evaluate got features only, expected labels
```

How DeepCTR's `input_fn_tfrecord` behaves:

- It parses all keys in `feature_description`.
- If `label` is not `None`, it does `labels = features.pop(label)` and returns `(features, labels)`.
- If `label` is `None`, it returns `features` only for prediction.

Actions:

- Include the label in `feature_description` when `label="label"`.
- Use the exact serialized key name, for example `"clicked"` if the TFRecord does not contain `"label"`.
- Use `label=None` only for prediction input functions.
- Keep labels scalar or shape `(1,)` and numeric. Binary labels should be `0/1` floats or integers convertible to floats.

## Pandas input missing dense default handling

Symptom examples:

```text
ValueError: could not convert string to float
Tensor conversion requested dtype float32 for object dtype column
Loss becomes nan early in training
```

Common causes:

- Dense columns contain `NaN`, strings, or mixed object dtype.
- Sparse columns were not label-encoded or hashed into valid integer IDs for identity columns.
- Test data contains an unseen categorical value encoded outside the training vocabulary.
- `features` passed to `input_fn_pandas` omits a model feature or includes the label incorrectly.

Actions:

```python
data[sparse_features] = data[sparse_features].fillna("-1")
data[dense_features] = data[dense_features].fillna(0.0).astype("float32")
# encode sparse IDs and cast to int64 before using identity feature columns
```

- Fit encoders on train data, preserve an unknown bucket for serving/test values, and set `num_buckets` high enough.
- Confirm `features=sparse_features + dense_features` and `label=label_name` for train/eval.
- For prediction, pass `label=None`; keep labels in the DataFrame only for external metric calculation if needed.

## Out-of-range categorical IDs

Symptom examples:

```text
indices[...] = ... is not in [0, num_buckets)
```

Actions:

- Compute `max_id` after preprocessing and set `num_buckets >= max_id + 1` per field.
- Reserve ID `0` for unknown/padding if needed and start valid IDs at `1`.
- For unstable or very high-cardinality raw IDs, prefer hash buckets and choose a large enough `hash_bucket_size`.

## Optimizer or training-op failures

Symptom examples:

```text
ValueError: Unsupported optimizer name
No variables to optimize
AttributeError around tf.train.get_global_step or tf.assign_add
```

Actions:

- Start with default `linear_optimizer="Ftrl"` and `dnn_optimizer="Adagrad"`.
- If passing optimizer instances, use optimizers compatible with the installed TensorFlow Estimator stack, often `tf.compat.v1.train.*Optimizer` in TF2-style environments with Estimator support.
- Ensure the selected model actually has feature columns for the parts you expect. `PNNEstimator` has no `linear_feature_columns` argument; most other constructors do.
- Run the tiny constructor probe; if constructor works but training fails, test with one batch of simple numeric/identity columns before scaling to real data.

## Large/distributed training expectations

DeepCTR Estimators are wrappers around TensorFlow Estimator. Large-scale behavior is not automatic just because `input_fn_tfrecord` is used.

Checklist:

- Shard TFRecord files explicitly and pass file lists/globs appropriate to the TensorFlow filesystem in use.
- Use `shuffle_factor` large enough for training but set it to `0` for deterministic evaluation over finite data.
- Set `num_epochs` deliberately. `num_epochs=1` is finite; repeated distributed training may need a different repeat/step plan.
- Tune `batch_size`, `num_parallel_calls`, and `prefetch_factor` against CPU/input throughput.
- Configure distributed workers, `RunConfig`, checkpoint location, and environment variables according to TensorFlow Estimator documentation for the installed TensorFlow version.
- Validate on one tiny local shard before launching a remote or multi-worker job.

## `model_dir` and checkpoint cleanup

Symptom examples:

```text
Assign requires shapes of both tensors to match
Key ... not found in checkpoint
Restoring from checkpoint failed after changing features
```

Common causes:

- Reused the same `model_dir` after changing feature names, bucket sizes, embedding dimensions, hidden units, model family, or `task`.
- Old checkpoints from a failed run remain in the directory.
- Multiple jobs write to the same `model_dir` unintentionally.

Actions:

- Use a new empty `model_dir` for each incompatible schema/model change.
- Keep `keep_checkpoint_max` small for experiments.
- Clean old temporary directories after failed smoke tests.
- For production, make checkpoint retention and worker ownership explicit; avoid shared scratch paths for concurrent experiments.

## When to fall back to Keras DeepCTR

Choose Keras-style DeepCTR workflows when:

- `tf.estimator` is missing.
- The project uses modern TensorFlow/Keras 3 where Estimator compatibility is not available.
- The task needs DeepCTR sequence models, multi-task Keras models, Keras callbacks, model saving/loading with `tensorflow.keras`, or in-memory NumPy/Pandas training without Estimator deployment semantics.
- You only need a small or medium CTR experiment and do not need Estimator input pipelines or checkpoint/distributed behavior.
