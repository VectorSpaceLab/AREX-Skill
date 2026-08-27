# Serving and Export Workflows

## Local FastAPI server

```bash
ludwig serve --model_path results/experiment_run/model --host 0.0.0.0 --port 8000 --prediction_timeout 30
```

Endpoints include single-row `/predict` and batch `/batch_predict` surfaces. Build payloads with the bundled helper and test batch prediction locally before starting a server.

## Payload shape

Single prediction generally maps input feature names to values. Batch prediction uses a list/table-like payload depending on endpoint/server variant. Image/audio fields may require file upload handling rather than plain JSON.

## Ray Serve and KServe

Ray Serve and KServe shims wrap Ludwig model loading and prediction. They require their service frameworks and often cluster/runtime configuration. Treat them as deployment integration, not a default local smoke test.

## vLLM serving

vLLM-style serving is for LLM model artifacts and requires compatible GPU/runtime/model support. Verify model type, quantization, max model length, tensor parallelism, and GPU memory first.

## Export and upload

- `export_model` supports `safetensors`, `torch_export`, and `onnx` formats. ONNX may need additional dependencies and model compatibility.
- `export_mlflow` requires MLflow-related dependencies.
- Hub upload requires credentials and creates remote state; dry-run planning should inspect paths and metadata only.
