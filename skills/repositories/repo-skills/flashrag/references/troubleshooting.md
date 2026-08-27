# FlashRAG Troubleshooting

## Fast Triage

1. Run the root checker: `python skills/flashrag/scripts/check_flashrag_environment.py --json`.
2. Validate input/config shape before running expensive work: use `data-and-config` for YAML/JSONL, `retrieval-and-indexing` for corpus/index commands, and `pipelines-and-methods` for method configs.
3. Identify whether the failure is core install/import, optional backend, data/config, model/index path, credentials/network, hardware, or service startup.
4. Follow the nearest sub-skill troubleshooting page for component-specific symptoms.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: flashrag` | Package not installed in the active Python | Install `flashrag-dev --pre` or an editable checkout, then rerun the import check. |
| Metadata lookup fails for `flashrag_dev` | Tool normalized distribution name to `flashrag-dev` | Try both names in diagnostics; public package is installed as FlashRAG distribution metadata. |
| `ModuleNotFoundError: yaml`, `numpy`, `torch`, `transformers`, or `tqdm` | Core/runtime dependency missing or partial install | Install FlashRAG runtime dependencies in the same environment used to run the workflow. |
| `pip check` reports conflicts | Mixed ML package stack or incompatible optional backend | Resolve package conflicts before debugging FlashRAG code; do not continue with a broken environment. |

## Optional Dependency Failures

| Workflow | Common missing pieces | Next step |
| --- | --- | --- |
| BM25 with Pyserini | `pyserini`, Java runtime | Prefer `bm25s` for lightweight CPU experiments unless Lucene/Pyserini behavior is required. |
| Dense retrieval | `faiss`, embedding model packages, model path | Verify `retrieval_model_path`, `index_path`, and CPU/GPU Faiss variant. |
| vLLM generation | `vllm`, compatible PyTorch/CUDA/GPU | Use HF/OpenAI/FastChat for config debugging; only install vLLM on compatible hardware. |
| OpenAI generation/evaluation | `openai`, `tiktoken`, API credentials | Use environment variables or secret manager; never hard-code credentials in skill notes. |
| Multimodal RAG | image packages, model-specific utilities, GPU memory | Validate modality fields and model family before loading the model. |
| WebUI | Streamlit/Gradio-style UI dependencies and valid configs | Check service dependencies and component config before launching the UI. |

## Data and Config Failures

- Corpus rows for retrieval should be JSONL documents with stable `id` and `contents` fields.
- Evaluation datasets should include task fields such as `question` and answer labels expected by the pipeline or metric.
- `Config` merges default settings, YAML file values, and dict overrides; dict overrides have highest priority.
- `Config` may prepare output directories unless `disable_save` is set in runtime overrides; use this for dry checks.
- Relative dataset, corpus, index, model, and save paths resolve in the user's runtime context, not inside this skill.

## Model, Index, and Hardware Failures

- Dense retrieval requires the index file to match the embedding model, pooling, dimensionality, and corpus used to build it.
- BM25 indexes are directories, not Faiss `.index` files.
- `faiss_gpu: true` requires GPU-capable Faiss and visible CUDA hardware; otherwise set it false.
- `gpu_id` changes visible CUDA devices for the process, but it does not install GPU packages or make CUDA available.
- Large model loading, index building, benchmark reproduction, and WebUI launches can download data or consume GPU memory; ask before running them in automation.

## Staleness and Refresh

Refresh this skill when public FlashRAG APIs, config keys, docs, examples, dependencies, optional extras, WebUI behavior, or CLI arguments change. The provenance file records the baseline commit and evidence paths used for this version.
