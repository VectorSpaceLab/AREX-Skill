# Sentence Transformers Troubleshooting

Use this root troubleshooting guide for cross-cutting package issues. For model-family or workflow-specific symptoms, open the nearest sub-skill troubleshooting reference.

## Install or Import Fails

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: sentence_transformers` | Package not installed in the active Python | Run `pip install -U sentence-transformers` and verify with the root import check. |
| `ModuleNotFoundError: datasets` or `accelerate` during training | Training extra missing | Install `pip install -U "sentence-transformers[train]"`. |
| Image/audio/video input fails at processor import | Multimodal extra missing | Install the relevant `[image]`, `[audio]`, or `[video]` extra; `torchcodec` may be needed for decoder objects. |
| ONNX import/provider error | ONNX extra or provider package missing | Use `sub-skills/backend-export-optimization/scripts/backend_export_check.py --signatures` and install `[onnx]` or `[onnx-gpu]`. |
| OpenVINO import/export error | OpenVINO extra missing | Install `sentence-transformers[openvino]` and read `sub-skills/backend-export-optimization/references/troubleshooting.md`. |

## Model Loading Fails

- For offline use, pass `local_files_only=True` or use the bundled scripts' `--local-files-only` flag only when the model is already cached or local.
- For private Hub models, pass a token through the supported package APIs or authenticate outside the script; do not hardcode tokens in code.
- If `trust_remote_code=True` is suggested by a model card, treat it as a security decision and ask before enabling it for untrusted models.
- If a download is slow or blocked, avoid repeatedly retrying in an agent loop; switch to a local model path or ask about network constraints.

## Choosing the Wrong Model Family

- Dense embeddings or first-stage search: `sub-skills/embeddings-and-similarity/SKILL.md` plus `sub-skills/retrieval-and-utilities/SKILL.md`.
- Pair scoring or reranking a short candidate list: `sub-skills/reranking-cross-encoder/SKILL.md`.
- Learned sparse vectors or SPLADE-style retrieval: `sub-skills/sparse-encoder-search/SKILL.md`.
- Loss/evaluator/trainer choices: `sub-skills/evaluation-and-training/SKILL.md`.

## Performance and Memory

- Increase throughput with batching, normalized embeddings for dot-product search, and precomputed corpus embeddings before considering heavier backends.
- Use CPU for small local embedding models when GPU memory is contested by a generative model.
- ONNX/OpenVINO acceleration is an optional deployment path, not a prerequisite for normal inference.
- Sparse search and vector databases may need service-specific packages and running services; keep these optional unless the user requests them.

## Safe Validation Order

1. Verify install/import with the root command.
2. Use a bundled script `--help` command to confirm CLI shape.
3. Run network-free helper modes such as `semantic_search_demo.py --toy-tensors`.
4. Only then run model-loading, training, export, or service integration checks when prerequisites are explicit.
