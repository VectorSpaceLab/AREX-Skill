---
name: encoding-retrieval
description: "Encode Tevatron queries and corpora, run FAISS retrieval, merge
  shard rankings, and plan retrieval evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Encoding and Retrieval

Use this sub-skill when a Tevatron workflow needs embedding files, FAISS search, shard-result merging, or a BEIR/MS MARCO/TREC evaluation plan after data is already in Tevatron-compatible query/corpus form.

## Start Here

1. Read [Encoding Reference](references/encoding.md) to choose the encoder driver, dataset flags, sharding plan, and embedding pickle checks.
2. Read [Search and Evaluation Reference](references/search-and-evaluation.md) to build FAISS search commands, merge per-shard rankings, and plan benchmark conversion/evaluation.
3. Read [Troubleshooting](references/troubleshooting.md) before changing FAISS/vLLM dependencies, batch sizes, glob patterns, output formats, or GPU settings.
4. Use [reduce_results.py](scripts/reduce_results.py) to merge text ranking shards and [tiny_faiss_search_smoke.py](scripts/tiny_faiss_search_smoke.py) for a no-model FAISS search smoke check.

## Scope

This sub-skill owns:

- Query and corpus encoding with `python -m tevatron.retriever.driver.encode`.
- Optional vLLM encoding with `python -m tevatron.retriever.driver.vllm_encode` when the vLLM stack is installed and the model supports embedding mode.
- Embedding pickle validation, corpus sharding, FAISS flat inner-product search, text vs pickle ranking outputs, CPU/GPU FAISS behavior, shard-result reduction, and BEIR/MS MARCO/TREC-style evaluation planning.

This sub-skill does not create dataset schemas, train retriever checkpoints, mine hard negatives, or run cross-encoder reranking. Use sibling sub-skills for data preparation, training, multimodal/LLM-specific setup, or reranking.

## Decision Checklist

- Confirm prepared inputs already expose query IDs/text for query encoding and document IDs/text for corpus encoding.
- Encode queries with `--encode_is_query`; omit it for corpus/passages.
- Keep model, tokenizer, pooling, normalization, prefix, LoRA adapter, dtype, padding side, and EOS-token choices aligned between query and corpus embeddings unless the task intentionally compares incompatible settings.
- Use `--dataset_number_of_shards` and `--dataset_shard_index` for large corpus fan-out; do not rely on Tevatron multi-GPU encoding because the standard encoder guards against multi-GPU evaluation.
- Use `--save_text` for downstream evaluation or shard merging; omit it only when a Python consumer explicitly expects the ranking pickle `(scores, passage_ids)`.
- Treat `faiss`, `torch`, `vllm`, CUDA, Pyserini, benchmark datasets, and model downloads as optional runtime requirements, not base Tevatron import guarantees.

## Bundled Helpers

- `scripts/reduce_results.py`: self-contained deterministic reducer for per-shard text rankings shaped as `qid pid score`.
- `scripts/tiny_faiss_search_smoke.py`: synthetic FAISS smoke test that skips with guidance when optional FAISS/Tevatron search dependencies are unavailable.
