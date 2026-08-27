---
name: tevatron
description: "Use Tevatron for neural retrieval workflows including data
  preparation, retriever training, encoding, FAISS retrieval, reranking, and
  multimodal or LLM retrievers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tevatron

Use this repo skill when a task mentions Tevatron, neural retrieval, dense retriever training, embedding query/corpus datasets, FAISS search, cross-encoder reranking, sparse retrievers, RepLLaMA/RankLLaMA, ColPali, DSE, Qwen, or multimodal retrieval data.

Tevatron is a Python toolkit for learning and running neural retrieval models across scale, language, and modality. This skill is self-contained: use the bundled references and scripts here instead of reopening the source repository.

## Quick Start

1. Choose the workflow route from the table below.
2. Confirm the package surface:
   ```bash
   python - <<'PY'
   import tevatron
   print("tevatron import ok")
   PY
   ```
3. Install only the optional dependencies needed by the selected route. Base metadata requires `transformers` and `datasets`; many practical workflows also need `torch`, `faiss-cpu` or `faiss-gpu`, `peft`, `deepspeed`, `accelerate`, `jax`/`flax`/`optax`, `vllm`, `Pillow`, or Qwen-specific utilities.
4. Run `python scripts/check_tevatron_environment.py --json` for a safe optional-dependency report before recommending heavyweight model, GPU, JAX, vLLM, or multimodal commands.
5. Read `references/troubleshooting.md` before broad dependency changes, GPU/JAX installs, model downloads, or long training/evaluation runs.

## Route by Task

| User task | Read next |
| --- | --- |
| Validate JSONL, corpus/query schemas, qrels, rankings, hard-negative inputs, or format conversions | `sub-skills/data-preparation/` |
| Build dense, sparse, distillation, GradCache, LoRA, DeepSpeed, or JAX training commands | `sub-skills/training/` |
| Encode query/corpus embeddings, shard outputs, run FAISS search, merge rankings, or plan BEIR/MS MARCO evaluation | `sub-skills/encoding-retrieval/` |
| Prepare pairwise rerank input, train a cross-encoder reranker, run reranking, or interpret reranker scores | `sub-skills/reranking/` |
| Work with ColPali, DSE/Qwen, Qwen2.5-VL, Qwen-Omni, Qwen3-Embedding, RepLLaMA, RankLLaMA, vLLM, images, audio, video, or asset paths | `sub-skills/multimodal-llm/` |

## Workflow Order

Most end-to-end retrieval tasks follow this order:

1. `sub-skills/data-preparation/`: validate train/query/corpus/rerank records and convert run files when needed.
2. `sub-skills/training/`: assemble a retriever training command or choose a pretrained checkpoint path.
3. `sub-skills/encoding-retrieval/`: encode query and corpus embeddings, run FAISS search, and merge shard outputs.
4. `sub-skills/reranking/`: optionally prepare pairwise candidates and rerank first-stage results.
5. `sub-skills/multimodal-llm/`: apply when any step uses media fields, Qwen-family processors, LLM retrievers/rankers, or vLLM.

## Bundled Root Files

- `references/repo-provenance.md`: read before deciding whether this skill is current for a Tevatron checkout or should be refreshed.
- `references/troubleshooting.md`: cross-cutting install/import, optional dependency, backend, data, and command failure guidance.
- `references/repo-routing-metadata.json`: structured metadata used by `repo-skills-router` during DisCo import.
- `scripts/check_tevatron_environment.py`: safe dependency/import probe for Tevatron workflows; it reports availability but does not download models or run training.

## Installation Guidance

Use a minimal install for inspection, data validation, command building, or format conversion:

```bash
pip install tevatron transformers datasets
```

For local development or a checkout, use editable installation from the checkout root:

```bash
pip install -e .
```

Then add route-specific dependencies only when needed:

- Encoding/search: `faiss-cpu` for CPU FAISS; GPU FAISS requires a compatible CUDA/FAISS stack.
- PyTorch training, encoding, and reranking: `torch`, plus `peft` for LoRA and `deepspeed`/`accelerate` for distributed or ZeRO runs.
- JAX/TPU routes: `jax`, `flax`, `optax`, and Tevax/Magix dependencies used by the selected experimental driver.
- Multimodal/Qwen routes: `Pillow`, Qwen utility packages, model processors, and sometimes `vllm` or FlashAttention.

Avoid installing all optional stacks at once unless the task explicitly needs them. Tevatron workflows are model- and backend-heavy; the safest route is to validate data and commands first, then install the exact backend required by the selected workflow.

## Safety and Validation

- Do not run training, model downloads, dataset downloads, BEIR evaluation, or GPU/vLLM/JAX jobs as quick checks unless the user explicitly asked for that execution.
- Use bundled scripts with tiny fixtures for deterministic checks before expensive runs.
- Treat original repository examples as evidence. Do not make runtime plans that depend on source checkout examples or scripts remaining available.
- If an optional dependency is missing, first read the owning sub-skill troubleshooting file and the root `references/troubleshooting.md`; do not paper over missing backend packages with unrelated installs.

## Common Routing Signals

- `--dataset_name json`, `--dataset_path`, `query_id`, `docid`, `positive_document_ids`, `negative_document_ids`: `sub-skills/data-preparation/`.
- `tevatron.retriever.driver.train`, `--grad_cache`, `--lora`, `--deepspeed`, `train_distil`, SPLADE, UniCOIL, Tevax: `sub-skills/training/`.
- `tevatron.retriever.driver.encode`, `--encode_is_query`, `--encode_output_path`, `tevatron.retriever.driver.search`, `--passage_reps`, `--save_ranking_to`: `sub-skills/encoding-retrieval/`.
- `tevatron.reranker.driver.train`, `tevatron.reranker.driver.rerank`, pairwise JSONL, RankLLaMA scoring: `sub-skills/reranking/`.
- `query_image`, `document_image`, `assets_path`, Qwen, ColPali, DSE, RepLLaMA, vLLM encode, FlashAttention, media processors: `sub-skills/multimodal-llm/`.
