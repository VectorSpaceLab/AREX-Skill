# Deployment API Reference

## `Engine.predict`

```python
engine.predict(
    model=None,
    dataloaders=None,
    datamodule=None,
    dataset=None,
    return_predictions=None,
    ckpt_path=None,
    data_path=None,
)
```

- `model` is required unless the engine already owns a model from a previous run.
- `dataloaders` accepts one `DataLoader` or a list of `DataLoader` objects.
- `dataset` accepts a `Dataset` or `PredictDataset` and is wrapped in a `DataLoader`.
- `data_path` is converted to `PredictDataset(data_path)` internally.
- `datamodule` is the Lightning path for prediction hooks and normalization.
- `ckpt_path` is optional; if omitted, the current model weights are used.
- Validation may run first when normalization or thresholds are needed.

## `Engine.export`

```python
engine.export(
    model,
    export_type,
    export_root=None,
    model_file_name="model",
    input_size=None,
    compression_type=None,
    datamodule=None,
    metric=None,
    max_drop=0.01,
    ov_args=None,
    ov_kwargs=None,
    onnx_kwargs=None,
    ckpt_path=None,
)
```

- `export_type` can be `"torch"`, `"onnx"`, or `"openvino"`.
- `ov_args` is deprecated; prefer `ov_kwargs`.
- `max_drop` only matters for `INT8_ACQ`.
- `datamodule` is required for `INT8_PTQ` and `INT8_ACQ`.
- `metric` is used for `INT8_ACQ`; if omitted, a default image-level F1Score is used.
- `ckpt_path` reloads the model before export.

## `ExportMixin`

```python
model.to_torch(export_root, model_file_name="model")
model.to_onnx(export_root, model_file_name="model", input_size=None, **kwargs)
model.to_openvino(
    export_root,
    model_file_name="model",
    input_size=None,
    compression_type=None,
    datamodule=None,
    metric=None,
    task=None,
    max_drop=0.01,
    ov_kwargs=None,
    onnx_kwargs=None,
)
```

- `to_torch` stores a pickled model object inside `weights/torch/model.pt`.
- `to_onnx` supports the legacy exporter and the `dynamo=True` path.
- `to_openvino` first exports ONNX, then converts to OpenVINO IR, then optionally compresses.
- `INT8_PTQ` and `INT8_ACQ` require a datamodule.
- `INT8_ACQ` can use a default `F1Score` metric when no metric is passed.

## Export and compression enums

### `ExportType`

- `ONNX = "onnx"`
- `OPENVINO = "openvino"`
- `TORCH = "torch"`

### `CompressionType`

- `FP16 = "fp16"`
- `INT8 = "int8"`
- `INT8_PTQ = "int8_ptq"`
- `INT8_ACQ = "int8_acq"`

## Inferencers

### `TorchInferencer(path, device="auto")`

- Legacy inferencer.
- Loads `.pt` or `.pth` checkpoints with `torch.load`.
- Requires `TRUST_REMOTE_CODE=1` for trusted files.
- Returns `ImageBatch` predictions.

### `OpenVINOInferencer(path, device="AUTO", config=None)`

- Accepts `.xml`, `.bin`, `.onnx`, or a tuple of model bytes.
- Uses OpenVINO `AUTO` by default.
- Returns `NumpyImageBatch` predictions.
- Creates or reuses an `openvino_cache/` directory in the current working directory.
