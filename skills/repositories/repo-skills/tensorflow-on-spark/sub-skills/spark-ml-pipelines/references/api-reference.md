# API Reference: Spark ML Pipelines

This reference covers DataFrame-backed training and inference only. The signatures and defaults below were verified from the installed `tensorflowonspark.pipeline` module and cross-checked against repository tests and example workflows.

## Verified surface

| Symbol | Verified signature | What to remember |
| --- | --- | --- |
| `pipeline.Namespace.__init__` | `(self, d)` | Accepts `dict`, `list`, `argparse.Namespace`, or `Namespace`. A list is preserved as `argv`. |
| `pipeline.TFParams.merge_args_params` | `(self)` | Copies `self.args` and overlays Spark ML params from `self.params`. |
| `pipeline.TFEstimator.__init__` | `(self, train_fn, tf_args, export_fn=None)` | Spark ML estimator wrapper. |
| `pipeline.TFModel.__init__` | `(self, tf_args)` | Spark ML model wrapper. |
| `pipeline.yield_batch` | `(iterable, batch_size, num_tensors=1)` | Batches partition rows for `mapPartitions` inference. |
| `TFCluster.InputMode` | `SPARK=1`, `TENSORFLOW=0` | The Spark ML pipeline API only supports SPARK. |
| `pipeline.HasInputMode.setInputMode` | n/a | Raises `Exception("InputMode.TENSORFLOW is deprecated")` if asked for TENSORFLOW. |
| `pipeline.TFTypeConverters.toDict` | n/a | `input_mapping` and `output_mapping` must be dicts. |
| `TFNode.export_saved_model` | `(sess, export_dir, tag_set, signatures)` | Legacy TF1 SavedModel export helper. |
| `compat.export_saved_model` | `(model, export_dir, is_chief=False)` | TF2-friendly SavedModel export helper used by the examples. |

## Training flow (`TFEstimator.fit`)

1. Build `TFEstimator(train_fn, tf_args)`.
2. Set `input_mapping` with DataFrame column names as keys and TensorFlow input tensor names as values.
3. `fit()` merges raw args with ML params, creates a `TFCluster` in `InputMode.SPARK`, and feeds `dataset.select(input_cols).rdd` into `cluster.train(...)` after sorting the mapping keys.
4. After training, the cluster shuts down with `grace_secs`.
5. If you set `export_fn`, it only works for TF1.x. Under TF2, the code raises `Please use native TF2.x APIs to export a saved_model.`

Important defaults from source:
- `input_mode=SPARK`
- `batch_size=100`
- `epochs=1`
- `cluster_size=1`
- `num_ps=0`
- `readers=1`
- `steps=1000`
- `grace_secs=30`
- `master_node='chief'` when TF >= 2.0.0

## Inference flow (`TFModel.transform`)

1. Build `TFModel(tf_args)`.
2. Set `input_mapping` and `output_mapping`.
3. For TF1, `input_cols` are sorted by DataFrame column name, `output_cols` by output tensor name.
4. For TF2, `_run_model_tf2` loads the SavedModel once per Python worker, caches `global_model` and `pred_fn`, and reshapes flat Spark inputs to the signature shapes.
5. `transform()` returns a new DataFrame created from `Row(*x)` values and `output_cols`.

### Deterministic ordering rules

- Training input selection uses `sorted(self.getInputMapping())`, so the dict key order is not semantic.
- Inference input selection uses `input_cols = [col for col, tensor in sorted(self.getInputMapping().items())]`.
- Inference output column order uses `output_cols = [col for tensor, col in sorted(self.getOutputMapping().items())]`.
- The output mapping therefore sorts by output tensor name, not by DataFrame column name.

## SavedModel selection rules

| Situation | Set these fields | What happens |
| --- | --- | --- |
| TF1 checkpoint | `model_dir` | Loads the latest checkpoint with `tf.train.latest_checkpoint`. |
| TF1 SavedModel | `export_dir`, `tag_set`, optional `signature_def_key` | Loads the meta graph for the requested tags, and uses the signature to resolve tensor names when `signature_def_key` is present. |
| TF2 SavedModel | `export_dir`, `tag_set`, `signature_def_key` | Uses `tf.saved_model.load(...).signatures[signature_def_key]` and cached per-worker `pred_fn`. |

Typical values:
- `tag_set='serve'`
- `signature_def_key='serving_default'`

## Batch and cache behavior

- `yield_batch()` can yield a smaller final batch.
- `bytearray` inputs are converted to strings before batching.
- Each Spark Python worker caches one model/session per compatible args object.
- Change `export_dir`, `tag_set`, or `signature_def_key` only when you want the cache to reload.
- The cache exists to avoid reloading the model for every partition.

## Source-backed reminders

- `TFEstimator.fit()` returns a `TFModel` seeded with the estimator args/params; set inference-specific mappings on the returned model before `transform()`.
- `TFEstimator.export_fn` is a TF1-only escape hatch. For TF2, export inside the training code with native SavedModel APIs or `compat.export_saved_model`.
- `setInputMapping()` and `setOutputMapping()` accept dicts only; non-dicts fail fast.
