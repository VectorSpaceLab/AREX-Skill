---
name: backend-export-optimization
description: "Use when selecting Sentence Transformers inference backends or
  exporting/optimizing models for PyTorch, ONNX, or OpenVINO. Covers
  backend=\"onnx\"/\"openvino\", optional extras, model_kwargs, optimized and
  quantized artifacts, and export troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Backend Export Optimization

Use this sub-skill when a user asks how to speed up inference with backend-level model formats, diagnose ONNX/OpenVINO installation or loading failures, or prepare optimized/quantized model artifacts for local use or Hugging Face Hub pull requests.

## Route Requests

- Choose `backend="torch"` for the default PyTorch path, GPU dtype tweaks such as `model_kwargs={"torch_dtype": "float16"}`, or simplest compatibility.
- Choose `backend="onnx"` when the user installed the `onnx` or `onnx-gpu` extra and wants ONNX Runtime inference, optimized ONNX files, or dynamic int8 ONNX quantization.
- Choose `backend="openvino"` when the user installed the `openvino` extra and targets Intel/CPU OpenVINO inference or static OpenVINO quantization.
- Use `model_kwargs={"provider": ...}` for ONNX Runtime execution providers and `model_kwargs={"file_name": ...}` to load a specific exported, optimized, or quantized artifact.
- Use `model.save_pretrained(...)` after exporting a local model and `model.push_to_hub(..., create_pr=True)` for Hub models so future loads do not re-export.

## Core References

- Backend workflow and API details: `references/backend-reference.md`
- Failure diagnosis and fixes: `references/troubleshooting.md`
- Environment/API check script: `scripts/backend_export_check.py`

## Quick Patterns

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    backend="onnx",
    model_kwargs={"provider": "CPUExecutionProvider"},
)
embeddings = model.encode(["backend export smoke test"])
model.push_to_hub("sentence-transformers/all-MiniLM-L6-v2", create_pr=True)
```

```python
from sentence_transformers import SentenceTransformer, export_optimized_onnx_model

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", backend="onnx")
export_optimized_onnx_model(
    model=model,
    optimization_config="O3",
    model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
    push_to_hub=True,
    create_pr=True,
)
```

## Important Boundaries

- Backend export quantizes or optimizes the model runtime artifact; output-vector quantization for retrieval storage/search is a separate workflow owned by retrieval utilities.
- ONNX/OpenVINO exports convert the Transformer component. If using exported files outside Sentence Transformers, reproduce pooling, normalization, SPLADE pooling, or CrossEncoder activation yourself.
- Do not use this sub-skill for training, evaluator routing, or generic semantic-search recipes except to validate that an exported backend still produces expected inference outputs.
