---
name: modeling-and-tokenization
description: "Use when inspecting ColBERT checkpoints, ColBERTConfig
  model/tokenizer fields, QueryTokenizer or DocTokenizer behavior,
  query/document max lengths, marker tokens, punctuation masking, embedding
  dimensions, or safe model/tokenizer import diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Modeling and Tokenization

Use this sub-skill when an agent needs to reason about ColBERT model checkpoints, tokenizer behavior, config compatibility, text-to-token tensorization, or query/document embedding shapes before indexing, searching, or training.

## Route Here For

- Inspecting `Checkpoint(name, colbert_config=None, verbose=3)` loading behavior and `checkpoint.colbert_config` values.
- Changing or debugging `ColBERTConfig` fields such as `query_maxlen`, `doc_maxlen`, `dim`, `mask_punctuation`, `attend_to_mask_tokens`, `query_token_id`, or `doc_token_id`.
- Understanding how `QueryTokenizer` and `DocTokenizer` insert `[Q]` and `[D]` markers, truncate text, pad queries with `[MASK]`, and return IDs/masks.
- Explaining `Checkpoint.queryFromText()` and `Checkpoint.docFromText()` output shapes, `to_cpu`, `keep_dims`, `return_tokens`, and packed document outputs.
- Diagnosing checkpoint metadata, tokenizer downloads, local-vs-Hugging Face model names, CPU/GPU model loading caveats, or missing optional dependencies.

## Start With

1. Read `references/modeling-and-tokenization.md` for the conceptual model, checkpoint/config merge behavior, marker tokens, tokenization, and embedding outputs.
2. Read `references/config-reference.md` before changing shape-sensitive fields such as `query_maxlen`, `doc_maxlen`, or `dim`.
3. Read `references/api-reference.md` for verified imports, constructor signatures, tensorizer methods, encoding outputs, and shape invariants.
4. Use `scripts/inspect_checkpoint_config.py` when you need a safe ColBERTConfig summary; pass `--allow-remote` only when remote Hugging Face access is intentional.
5. Use `scripts/tokenization_smoke.py` when a local checkpoint or explicitly allowed model name should be checked for marker placement, truncation, and tensor shapes.
6. Read `references/troubleshooting.md` when imports, checkpoint metadata, Hugging Face downloads, max-length truncation, punctuation masking, or device behavior is surprising.

## Boundaries

- This sub-skill covers modeling, config, checkpoint, tokenizer, and embedding-inspection tasks.
- For full indexing/search orchestration, index roots, ranking, or `Indexer`/`Searcher` usage, route to the indexing-and-search sub-skill.
- For training, triples, distillation, optimizer settings, checkpoint creation, or `Trainer`, route to the training-and-distillation sub-skill.
- For collection/query/ranking file schemas beyond text passed into tokenizers, route to the data-and-evaluation sub-skill.

## Operating Cautions

- Prefer local checkpoint directories for deterministic inspection. Hugging Face model names such as `colbert-ir/colbertv2.0` or `bert-base-uncased` can require network/cache access.
- `ColBERTConfig.load_from_checkpoint()` can return `None` for a generic Hugging Face backbone or a checkpoint directory missing ColBERT `artifact.metadata`.
- Query and document marker IDs are inserted at column `1`; do not pre-insert marker IDs before calling ColBERT tensorizers.
- Query tensor width is normally `query_maxlen`; document tensor width is capped by `doc_maxlen` but may be the longest sequence in the batch, not always exactly `doc_maxlen`.
- CPU-only import/config inspection is safe; full model loading can compile a small CPU extension, download tokenizer/model files, or hit torch/transformers compatibility issues.
