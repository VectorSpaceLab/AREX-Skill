# MultiModal Deployment and Export

## Save and Load

```python
predictor.save("model_dir", standalone=True)
loaded = MultiModalPredictor.load("model_dir", resume=False, verbosity=3)
```

Use `standalone=True` when the saved model should include downloaded transformer/vision assets for offline deployment. Use `standalone=False` only when the deployment environment can access the same model checkpoints later.

Security note: `MultiModalPredictor.load` uses pickle-backed artifacts. Only load directories that the user trusts.

## Export ONNX

`export_onnx` traces the model with representative raw input data and returns either bytes or a file path.

```python
onnx_bytes = predictor.export_onnx(data=sample_df)
onnx_path = predictor.export_onnx(data=sample_df, path="model.onnx", opset_version=16)
```

For image models, pass representative image input, for example `{"image": ["example.jpg"]}`. For text models, pass a DataFrame or dict with the same text columns used by the predictor. Keep the sample small but representative enough to exercise preprocessing.

Important constraints:

- The predictor's underlying model must be initialized; for trained predictors this usually happens naturally, and `export_onnx` calls prediction setup internally.
- ONNX export is not guaranteed for every model family or custom configuration.
- `path=None` returns bytes instead of writing to disk.
- `batch_size` can be set for tracing; dynamic axes are normally intended for variable batch sizes.
- `truncate_long_and_double=True` can help with unsupported int64/float64 weights at the cost of casting.

## Optimize for Inference

```python
predictor.optimize_for_inference(providers=None)
```

This converts the PyTorch module to an ONNX-backed module for inference. If `providers=None`, ONNXRuntime will try efficient providers in priority order when available, including TensorRT, CUDA, then CPU depending on installation. Explicit providers are safer in controlled deployments:

```python
predictor.optimize_for_inference(providers=["CPUExecutionProvider"])
predictor.optimize_for_inference(providers=["CUDAExecutionProvider"])
predictor.optimize_for_inference(providers=["TensorrtExecutionProvider", "CUDAExecutionProvider"])
```

Use TensorRT only when the installed `onnxruntime-gpu`, TensorRT, CUDA, cuDNN, PyTorch, and GPU driver versions are known compatible.

## Feature Extraction for Downstream Systems

For retrieval, clustering, or external services, use embeddings instead of raw model internals:

```python
embeddings = predictor.extract_embedding(data, as_tensor=False, as_pandas=False)
```

For matchers with query/response-specific preprocessing, pass the correct side through `signature` when needed:

```python
query_vectors = matcher.extract_embedding(query_df, id_mappings=id_mappings, signature="query")
response_vectors = matcher.extract_embedding(response_df, id_mappings=id_mappings, signature="response")
```

## Packaging Checklist

- Save to an explicit model directory and record the AutoGluon package version externally in deployment metadata.
- Prefer `standalone=True` for offline deployment.
- Verify imports on the target machine before loading a predictor.
- Verify torch/torchvision compatibility before image, detection, or segmentation deployment.
- For ONNX, verify `onnxruntime` providers with `scripts/multimodal_smoke.py --optional-backends`.
- Use small representative samples for export/optimization tests.
- Never load predictor artifacts from untrusted sources.

## Optional Backend Matrix

| Deployment goal | Likely optional dependencies | Notes |
| --- | --- | --- |
| CPU text/image inference | matching `torch` and `torchvision`, transformers checkpoints | CPU can be slow but useful for validation. |
| Document inference | OCR/PDF dependencies, transformer document checkpoints | PDFs may need Poppler or OCR tooling. |
| Object detection | MMDetection/MMCV stack, pycocotools/torchmetrics | Version compatibility is critical. |
| Semantic segmentation | segmentation checkpoint dependencies, PyTorch image stack | GPU is usually expected for useful speed. |
| ONNX CPU | `onnx`, `onnxruntime` | Export support depends on model family. |
| ONNX CUDA | `onnxruntime-gpu`, CUDA-compatible PyTorch | Check provider availability. |
| TensorRT | TensorRT plus compatible ONNXRuntime GPU build | Treat as advanced deployment, not default. |

## Deployment Failure Patterns

- `No module named onnxruntime`: install the ONNXRuntime variant that matches CPU/GPU requirements.
- Provider not found: requested ONNXRuntime provider is not compiled into the installed package.
- TensorRT segmentation fault or engine build failure: version mismatch; fall back to CUDA or CPU provider.
- Different predictions after ONNX conversion: validate preprocessing columns and compare with tolerances on a small sample.
- Load fails after moving machines: package versions or checkpoint assets differ; use standalone saves and recreate the environment.
- Network access during load: predictor was saved without all assets or checkpoint cache is missing.
