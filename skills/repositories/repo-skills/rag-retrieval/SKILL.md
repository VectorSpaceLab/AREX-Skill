---
name: rag-retrieval
description: "Use RAG-Retrieval for RAG reranker inference plus bundled
  preparation for embedding, reranker, and ColBERT retrieval-model training
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RAG-Retrieval

Use this repo skill when a user asks about RAG-Retrieval, `rag_retrieval`, RAG passage reranking, retrieval-model fine-tuning, BGE/BCE reranker scoring, embedding training, reranker distillation, or ColBERT-style late-interaction training.

RAG-Retrieval has two important surfaces:

- The installed `rag_retrieval` package exposes a lightweight reranker inference API centered on `Reranker`.
- The embedding, reranker, ColBERT, and distillation training workflows are source-code workflows; this skill bundles adapted snapshots and command builders because the current package metadata does not declare those training folders as installed packages.

## Route by Task

- **Rerank documents or score query-document pairs**: Use `sub-skills/inference/SKILL.md` for `Reranker`, `compute_score`, `rerank`, `RankedResults`, model type selection, long-document handling, and no-download API checks.
- **Fine-tune embedding models**: Use `sub-skills/embedding-training/SKILL.md` for pair/triplet/pair-score JSONL, MRL, `training_embedding.yaml`, FSDP/DeepSpeed choices, bundled training snapshots, and preflight validation.
- **Distill teacher embeddings**: Use `sub-skills/embedding-training/SKILL.md` for teacher text JSONL, float32 memmap shape checks, teacher embedding merge helpers, and `distill_embedding.yaml` validation.
- **Train BERT or LLM rerankers**: Use `sub-skills/reranker-training/SKILL.md` for pointwise/grouped JSONL, `loss_type`, BERT vs LLM decoder configs, RankNet/listwise losses, and LLM-to-BERT distillation planning.
- **Train ColBERT-style models**: Use `sub-skills/colbert-training/SKILL.md` for triplet JSONL, `neg_nums`, `colbert_dim`, FSDP layer choices, and the current package ColBERT inference limitation.
- **Investigate MyopicTrap or positional-bias experiments**: Read `references/research-benchmarks.md`; those scripts are research evidence and usually require external datasets, optional packages, credentials, or long benchmark runs.

## Start Here

1. Determine whether the user wants installed-package inference or bundled training preparation.
2. For installed-package inference, install the public package when needed:
   ```bash
   pip install rag-retrieval
   ```
3. Run the no-download package surface check when import/API drift matters:
   ```bash
   python scripts/check_rag_retrieval_install.py
   ```
4. For inference tasks, never instantiate a Hugging Face model just to inspect API shape; use the inference smoke script first.
5. For training tasks, validate configs and JSONL data with the owning sub-skill script before launching `accelerate`.
6. Treat model downloads, GPU jobs, benchmarks, and distillation data generation as expensive actions that need explicit user intent.

## Important Current Limitations

- `Reranker(model_type="colbert")` is not a working installed-package inference path in the inspected version: the mapping name exists, but the available ranker registry contains cross-encoder and LLM rankers only.
- The public factory class is spelled internally as `CorssEncoderRanker`; use the public `model_type="cross-encoder"` route in user-facing code.
- Empty `rerank` inputs can return a legacy dict instead of `RankedResults`; callers should handle that edge case.
- Training execution requires ML training dependencies and user data/model paths; this skill bundles selected training script snapshots and validation/command-building helpers, while an external current checkout can still be used explicitly for repo maintenance.

## Reference Map

- `references/package-overview.md`: Project surfaces, dependency notes, public APIs, and bundled training split.
- `references/troubleshooting.md`: Cross-cutting install/import, model download, optional dependency, data/config, GPU/backend, and routing failures.
- `references/research-benchmarks.md`: MyopicTrap and other benchmark/data-generation evidence that should usually stay reference-only.
- `references/repo-provenance.md`: Source commit, package version, evidence paths, and refresh baseline.
- `references/repo-routing-metadata.json`: Structured router metadata for managed import.
- `scripts/check_rag_retrieval_install.py`: Safe package/import/API surface check.

## Validation Defaults

- Prefer no-download checks first: package import, signatures, YAML parsing, JSONL schema validation, and helper `--help` output.
- Run native tests only after the whole skill is integrated and only when model caches, GPU availability, and expected runtime are acceptable.
- Skip or explicitly gate MyopicTrap, FlashRAG synthetic data generation, model downloads, LLM scoring, and full training runs unless the user authorizes expensive dependencies and runtime.

## Sub-Skill Boundaries

- `inference` owns installed-package `Reranker` behavior and result interpretation.
- `embedding-training` owns embedding fine-tuning, teacher embedding distillation, MRL, bundled training snapshots, and teacher-array helpers.
- `reranker-training` owns BERT/LLM reranker fine-tuning, ranking losses, pointwise/grouped data, bundled training snapshots, and LLM-to-BERT distillation planning.
- `colbert-training` owns bundled ColBERT training snapshots and explicitly routes packaged ColBERT inference questions back to the current inference limitation.
