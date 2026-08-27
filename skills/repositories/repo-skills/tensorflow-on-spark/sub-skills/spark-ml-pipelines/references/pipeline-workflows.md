# Pipeline Workflows

These workflows mirror the bundled MNIST pipeline examples but keep orchestration out of scope. Use them to build or recover a DataFrame-based pipeline skeleton.

## 1. Train a `TFEstimator` on a Spark DataFrame

**Inputs**
- Training DataFrame
- `train_fn(args, ctx)`
- `tf_args`
- `input_mapping`
- `cluster_size`, `batch_size`, `epochs`, `model_dir`, `export_dir`, `grace_secs`

**Flow**
1. Define `input_mapping` as a dict of DataFrame column name -> TensorFlow input tensor.
2. Implement `train_fn(args, ctx)` so it consumes batches from `TFNode.DataFeed(ctx.mgr, input_mapping=args.input_mapping)`.
3. Build `TFEstimator(train_fn, args)` and set the mapping, cluster size, batch size, epochs, model directory, export directory, and grace period.
4. Call `fit(train_df)`.
5. If you need a TF2 SavedModel, export inside your training code with native TF2 APIs or `compat.export_saved_model(...)`.

**Validation**
- `model_dir` exists after training.
- `export_dir` exists when export is enabled.
- A tiny follow-up `transform()` or `saved_model` load succeeds.

**Skeleton shape**
```python
INPUT_MAPPING = {
    "<df_column>": "<input_tensor>",
}

estimator = (
    TFEstimator(train_fn, args)
    .setInputMapping(INPUT_MAPPING)
    .setClusterSize(args.cluster_size)
    .setBatchSize(args.batch_size)
    .setEpochs(args.epochs)
    .setModelDir(args.model_dir)
    .setExportDir(args.export_dir)
)
# model = estimator.fit(train_df)
```

## 2. Run batch inference with `TFModel`

**Inputs**
- Trained checkpoint or SavedModel
- Inference DataFrame
- `input_mapping`
- `output_mapping`
- `batch_size`
- `model_dir` or `export_dir`
- `tag_set` and `signature_def_key` for SavedModels

**Flow**
1. Create `TFModel(tf_args)`.
2. Set the input mapping.
3. Set the output mapping.
4. For SavedModel inference, also set `tag_set` and `signature_def_key`.
5. Call `transform(test_df)`.

**Validation**
- Output columns match the `output_mapping` values.
- Row count matches input row count.
- Sample predictions have the expected shape and dtype.

**Skeleton shape**
```python
INPUT_MAPPING = {
    "<df_column>": "<input_tensor>",
}
OUTPUT_MAPPING = {
    "<output_tensor>": "<df_column>",
}

model = (
    TFModel(args)
    .setInputMapping(INPUT_MAPPING)
    .setOutputMapping(OUTPUT_MAPPING)
    .setBatchSize(args.batch_size)
    .setModelDir(args.model_dir)
    .setExportDir(args.export_dir)
    .setTagSet(args.tag_set)
    .setSignatureDefKey(args.signature_def_key)
)
# preds = model.transform(test_df)
```

## 3. Choose the right SavedModel path

- `model_dir` → checkpoint-backed inference.
- `export_dir` + `tag_set` → SavedModel-backed inference.
- `signature_def_key` lets the pipeline resolve signature tensor names instead of raw `:0` tensor names.
- Use `serve` / `serving_default` when the export tool wrote the default serving signature.

## 4. Render a skeleton

Generate a starter file without training execution:

```bash
python scripts/render_pipeline_template.py \
  --mode both \
  --input-mapping image:image \
  --input-mapping label:label \
  --output-mapping logits:prediction \
  --output pipeline_stub.py
```

The renderer only writes code. Fill in the placeholders for the DataFrame loader and TensorFlow training/inference bodies before use.

## 5. Source-backed example patterns

- `examples/mnist/keras/mnist_pipeline.py` shows `setInputMapping({'image': 'image', 'label': 'label'})` for train and `setInputMapping({'image': 'conv2d_input'}).setOutputMapping({'dense': 'cout'})` for inference.
- `examples/mnist/estimator/mnist_pipeline.py` shows the same pipeline shape with `setOutputMapping({'logits': 'prediction'})` and `signature_def_key='serving_default'`.
