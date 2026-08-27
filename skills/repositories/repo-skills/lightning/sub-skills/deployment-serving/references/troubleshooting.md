# Deployment Serving Troubleshooting

Use this reference when prediction, export, or serving validation fails. Do not assume GPU, TensorRT, or external service validation unless the environment explicitly proves it.

## Import and Version Failures

### `ModuleNotFoundError: No module named 'lightning'`

Install Lightning in the active Python environment:

```bash
python -m pip install "lightning[pytorch]"
```

Use current public imports in new code:

```python
import lightning as L
from lightning.pytorch import Trainer, LightningModule
```

Legacy code may still use `pytorch_lightning`; avoid rewriting stable user code only for style unless the task asks for modernization.

### Package version mismatch

The repo skill targets Lightning 2.6.x APIs. If an environment has an older package, verify the serving exports before relying on newer signatures:

```bash
python - <<'PY'
import lightning
print(lightning.__version__)
from lightning.pytorch.serve import ServableModule, ServableModuleValidator
print(ServableModule, ServableModuleValidator)
PY
```

If `lightning.pytorch.serve` is missing, upgrade Lightning or avoid the validator route.

## Optional Dependency Failures

### `requests` import failure

`ServableModuleValidator` imports `requests` in the serving validator module. Install it if the import fails:

```bash
python -m pip install requests
```

### `fastapi` or `uvicorn` missing

The validator constructor checks `fastapi` and `uvicorn` even before a server starts.

```bash
python -m pip install fastapi uvicorn requests
```

If the project only needs shape/serialization validation and not a local HTTP server, run:

```bash
python sub-skills/deployment-serving/scripts/servable_smoke.py --check-shape
```

### ONNX runtime/export missing

Typical signals include `ModuleNotFoundError: No module named 'onnx'`, `No module named 'onnxruntime'`, or export errors from unsupported operators.

- Install `onnx` for export.
- Install `onnxruntime` only when executing ONNX artifacts locally.
- Compare ONNX output to eager output with fixed inputs before shipping.
- If unsupported ops block export, consider `torch.export`, pure PyTorch, or simplifying the exported method.

### Quantization dependency missing

Intel Neural Compressor examples require `neural-compressor` and compatible Python/hardware support.

```bash
python -m pip install neural-compressor
```

Do not make quantization a mandatory dependency for ordinary prediction or serving-validator tasks.

## `ServableModuleValidator` Failures

### `NotImplementedError: Only the fastapi server is currently supported.`

Current source accepts server names such as `ml_server`, `torchserve`, and `sagemaker` in the type signature, but only `server="fastapi"` is implemented. Use FastAPI validation or write a custom integration test for the chosen serving platform.

### `NotImplementedError: The optimization ... is currently not supported.`

Current source raises this for any non-`None` optimization, including `trace`, `script`, `onnx`, and `tensorrt`. Validate those export paths separately with `references/export-workflows.md`.

### `The provided model should be subclass of ServableModule`

The model passed to the validator must be a `LightningModule` and a `ServableModule` implementation.

```python
from lightning.pytorch import LightningModule
from lightning.pytorch.serve import ServableModule

class MyServable(LightningModule, ServableModule):
    ...
```

### Missing serving hooks

The validator checks that these methods are overridden:

- `configure_payload`
- `configure_serialization`
- `serve_step`

`configure_response` is abstract on `ServableModule` and should also be implemented for deterministic validation.

### Payload missing `body`

The validator expects:

```python
def configure_payload(self):
    return {"body": {"x": [1.0, 2.0]}}
```

A payload such as `{"x": ...}` fails because the validator posts the full payload to `/serve` and the server reads `payload["body"]`.

### Response mismatch

If the failure says expected response does not match generated response:

- Confirm `serve_step` returns a dictionary.
- Confirm serializer keys match `serve_step` output keys.
- Make the test deterministic with fixed weights and fixed payload.
- Keep JSON types stable: tensors must become lists, floats, ints, strings, or nested JSON structures.

### Server did not start before timeout

Common causes:

- `fastapi`, `uvicorn`, or `requests` is missing.
- The selected port is already in use.
- The model is not picklable or has non-picklable runtime state when moved into the server process.
- The service startup takes longer than `timeout`.

Fixes:

```python
ServableModuleValidator(host="127.0.0.1", port=8099, timeout=60)
```

Also reduce payload/model size for validation; the validator is a sanity check, not a load test.

### FSDP or DeepSpeed strategy failure

The validator rejects `FSDPStrategy` and `DeepSpeedStrategy` sanity serving. Use a CPU/single-process validator smoke for the servable contract, then validate distributed training or large-checkpoint behavior separately through `../distributed-accelerators/SKILL.md`.

## Prediction Loop Failures

### Multiple dataloaders and missing `dataloader_idx`

If `Trainer.predict` fails with a message about `dataloader_idx`, update hook signatures:

```python
def predict_step(self, batch, batch_idx, dataloader_idx=0):
    return self(batch)
```

Do the same for prediction callbacks that receive dataloader-specific events.

### Predictions consume too much memory

Use `return_predictions=False` and a `BasePredictionWriter` to write outputs on each rank instead of aggregating them in memory.

```python
trainer.predict(model, dataloaders=loader, return_predictions=False)
```

### Stochastic or inconsistent predictions

- Call `model.eval()` for direct inference.
- Use `torch.inference_mode()` or `torch.no_grad()`.
- Seed random inputs in smoke tests.
- If Monte Carlo dropout is intentional, enable dropout inside `predict_step` and document that outputs are stochastic.

## Checkpoint Loading Failures

### Constructor argument mismatch

`load_from_checkpoint` reconstructs the LightningModule. If the checkpoint lacks required constructor arguments, pass them explicitly:

```python
model = LitModel.load_from_checkpoint("best_model.ckpt", hidden_dim=128, num_classes=10)
```

### State dict key mismatch in pure PyTorch conversion

Inspect checkpoint keys before remapping:

```python
checkpoint = torch.load("best_model.ckpt", map_location="cpu")
print(list(checkpoint["state_dict"].keys())[:20])
```

Common fix: remove a wrapper prefix such as `"model."`, `"net."`, or `"auto_encoder."` only if the production `nn.Module` does not include that prefix.

### Device-specific checkpoint load failure

Use CPU mapping for portable inference scripts:

```python
checkpoint = torch.load("best_model.ckpt", map_location="cpu")
```

Route GPU visibility, precision, and accelerator issues to `../distributed-accelerators/SKILL.md`.

## Export Failures

### Dynamic Python behavior blocks graph export

Export routes require graph-friendly code. Move logging, file I/O, tokenizer calls, and Python-only preprocessing outside the exported function. Export `forward` or a small wrapper around `predict_step` that accepts tensors and simple Python values.

### Shape mismatch after export

- Recheck `example_input_array` or `input_sample` shape.
- Validate both batch size and feature dimensions.
- Use representative inputs, not arbitrary placeholders.
- Add explicit reshape logic in `forward` if the model expects flattened tensors.

### Hardware/backend claims

CPU import and shape checks do not validate GPU, TensorRT, CUDA, ROCm, TPU, or MPS runtime behavior. If the user asks for those deployment targets, state the required backend checks and route hardware setup to `../distributed-accelerators/SKILL.md` when needed.

## Minimal Diagnostic Commands

```bash
python sub-skills/deployment-serving/scripts/servable_smoke.py --help
python sub-skills/deployment-serving/scripts/servable_smoke.py --check-shape
python - <<'PY'
from lightning.pytorch.serve import ServableModuleValidator
cb = ServableModuleValidator(port=8099, timeout=5)
print(cb.state_dict())
PY
```

The last command requires `fastapi`, `uvicorn`, and `requests`; it constructs the callback but does not validate a model by itself.
