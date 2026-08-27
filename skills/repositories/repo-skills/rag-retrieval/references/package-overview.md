# Package Overview

RAG-Retrieval provides code for RAG retrieval model inference, training, and distillation. The repo combines a small installed reranker package with source-code training workflows for embedding models, rerankers, and ColBERT-style late-interaction models. This skill bundles selected training snapshots and command builders so future agents are not forced to reopen the original checkout for routine workflow preparation.

## Installed Package Surface

Distribution metadata inspected for this skill:

- Distribution name: `rag_retrieval`
- Version: `0.2.2`
- Import module: `rag_retrieval`
- Public root export: `Reranker`
- Declared runtime dependencies: `pydantic`, `tqdm`, `torch`, `transformers`
- No console scripts are declared.

Important public signatures:

```python
from rag_retrieval import Reranker

ranker = Reranker(model_name, model_type=None, verbose=1, **kwargs)
```

`model_type` can be `cross-encoder` or `llm` for working installed inference routes in the inspected version. The source contains a `colbert` mapping name, but a working `ColBERTRanker` is not registered in the installed ranker registry.

Use `sub-skills/inference/SKILL.md` for detailed scoring, reranking, long-document handling, and result object behavior.

## Bundled Training Surface

Training workflows are documented and implemented as source scripts rather than installed package APIs. This skill bundles selected snapshots under each training sub-skill's `scripts/training_bundle/` directory plus shared accelerate configs under `scripts/accelerate_configs/`.

- Embedding training: pair/triplet/pair-score JSONL, MRL, normal fine-tuning, and teacher-embedding distillation.
- Reranker training: pointwise/grouped JSONL, BERT encoder or LLM decoder models, pointwise/pairwise/listwise losses, and LLM-to-BERT distillation planning.
- ColBERT training: triplet JSONL, late-interaction `colbert_dim`, FSDP/accelerate launch, and bundled/source-code scoring.

Use the owning training sub-skill before giving commands. The bundled validators are safe preflight tools; they do not download models or run training. The bundled command builders default to the skill-owned snapshots and accept `--checkout` only when the user explicitly wants to run against a current source checkout.

## Dependency Expectations

For inference:

- A Python environment with `rag_retrieval`, `torch`, and `transformers` is required.
- Hugging Face model names may trigger network downloads unless users pass local model paths or already have caches.
- Device selection is automatic unless `device` is passed; dtype can be `fp32`, `fp16`, or `bf16` depending on hardware and model support.

For training:

- Use the bundled training snapshots or an explicit current checkout plus training dependencies such as `accelerate`, `sentence_transformers`, `torch`, `transformers`, and `tqdm`.
- Choose FSDP for BERT/XLM-RoBERTa-style models and DeepSpeed for larger LLM-style models when needed.
- Match the accelerate config transformer layer class to the backbone family.
- Validate JSONL schemas and YAML before any GPU launch.

## Data Families

- Embedding pair: one `query` plus `pos` texts; random in-batch negatives are used.
- Embedding triplet / ColBERT triplet: one `query`, `pos` list, and `neg` list.
- Embedding pair-score: one `query`, `pos` list, and `scores` list.
- Embedding distillation: one `query` per line plus a float32 teacher embedding array with matching row count.
- Reranker pointwise: `query`, `content`, and a label key.
- Reranker grouped: `query` plus `hits`, where each hit has `content` and a label key.

## Safe Validation Helpers

- `scripts/check_rag_retrieval_install.py`: package/import/API surface check.
- `sub-skills/inference/scripts/reranker_api_smoke.py`: no-download inference API smoke.
- `sub-skills/embedding-training/scripts/validate_embedding_training_config.py`: embedding YAML/JSONL/teacher array validation.
- `sub-skills/embedding-training/scripts/merge_teacher_embeddings.py`: safe teacher embedding array concatenation.
- `sub-skills/reranker-training/scripts/validate_reranker_training_config.py`: reranker config/data/loss preflight.
- `sub-skills/colbert-training/scripts/validate_colbert_training_args.py`: ColBERT triplet data and argument preflight.

## What Not To Do

- Do not claim the installed package includes training entrypoints as importable modules; use bundled snapshots or an explicit checkout for training execution.
- Do not claim installed-package ColBERT inference works unless a current source version registers a working `ColBERTRanker`.
- Do not run benchmarks, full training, model downloads, or distillation generation as a casual smoke check.
- Do not rely on this skill’s validation scripts to replace a real small training smoke run when the user is ready to launch training.
