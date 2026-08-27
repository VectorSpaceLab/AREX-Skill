---
name: data-preparation
description: "Prepare and validate Tevatron JSON/JSONL datasets, rankings,
  qrels, hard-negative inputs, rerank inputs, and ranking conversion outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tevatron Data Preparation

Use this sub-skill when the task is to prepare, inspect, validate, repair, or convert files before Tevatron training, encoding, retrieval evaluation, or reranking. It covers local JSON/JSONL loading, Hugging Face dataset loading, train/corpus/query schemas, ID-list data with separate corpora, qrels/rankings, hard-negative prerequisites, rerank input bridges, and tiny local ranking conversions.

## Fast Path

1. Identify the downstream consumer:
   - Retriever training accepts either embedded `positive_passages`/`negative_passages`, compact `positive_document_ids`/`negative_document_ids` plus a corpus, or pre-tokenized rows.
   - Retriever encoding accepts query rows with `query_id` plus `query_text` or `query`, or corpus rows with `docid` plus text/media fields.
   - Reranker inference accepts one query-document pair per JSONL row with `query_id`, `query`, `docid`, `title`, and `text`.
   - Retrieval evaluation and hard-negative mining consume ranking/qrels files whose delimiters must match the target tool.
2. Decide loader mode:
   - Local JSONL: use `--dataset_name json --dataset_path <file.jsonl>`.
   - Local ID-list training: add `--corpus_name json --corpus_path <corpus.jsonl>` so document IDs can be resolved.
   - Hosted Tevatron/Hugging Face data: use `--dataset_name <namespace/name>` with optional `--dataset_config`, `--dataset_split`, and cache flags.
3. Validate local files from this sub-skill directory before expensive runs:
   - `python scripts/validate_tevatron_jsonl.py --kind train --input train.jsonl --corpus corpus.jsonl`
   - `python scripts/validate_tevatron_jsonl.py --kind corpus --input corpus.jsonl`
   - `python scripts/validate_tevatron_jsonl.py --kind query --input queries.jsonl`
   - `python scripts/validate_tevatron_jsonl.py --kind ranking --input rank.tsv --corpus corpus.jsonl`
   - `python scripts/validate_tevatron_jsonl.py --kind qrels --input qrels.txt --corpus corpus.jsonl`
   - `python scripts/validate_tevatron_jsonl.py --kind rerank --input rerank.jsonl`
4. Convert retrieval rankings when evaluation or submission tooling needs another format:
   - `python scripts/convert_result_to_trec.py --input rank.tsv --output rank.trec`
   - `python scripts/convert_result_to_marco.py --input rank.tsv --output rank.marco.tsv`
5. Route after validation:
   - Training command assembly: `../training/`.
   - Embedding/search execution and ranking generation: `../encoding-retrieval/`.
   - Pairwise reranker scoring: `../reranking/`.
   - Media-model dependencies, Qwen/ColPali/DSE, and optional multimodal execution: `../multimodal-llm/`.

## Key References

- `references/data-formats.md`: accepted record schemas, loader flags, qrels/ranking formats, local-vs-hosted dataset decisions, and multimodal-ish fields.
- `references/hard-negatives.md`: hard-negative mining inputs, top-k/min-count requirements, ID consistency checks, and rerank input bridge requirements.
- `references/troubleshooting.md`: fixes for malformed JSONL, missing IDs/text, corpus pairing mistakes, delimiter mismatches, hard-negative shortages, and missing media assets.

## Bundled Scripts

- `scripts/validate_tevatron_jsonl.py`: static validator for train, corpus, query, rerank, ranking, and qrels files; it performs no Tevatron imports, model loads, or network calls.
- `scripts/convert_result_to_trec.py`: standalone converter from Tevatron-style rankings to six-column TREC run format.
- `scripts/convert_result_to_marco.py`: standalone converter from Tevatron-style rankings to MS MARCO `qid<TAB>docid<TAB>rank` format.

## Safe Defaults

- Keep IDs as strings across train rows, corpus rows, rankings, qrels, and rerank inputs.
- Keep ranking files grouped by query in desired rank order before conversion; converters recompute rank per contiguous query block.
- For default `train_group_size=8`, plan at least seven usable negatives per query after removing positives and duplicate/invalid docids.
- Treat hosted datasets as network/cache-dependent unless the working environment already has the dataset cached.
- Check media path fields with `--assets-root` before multimodal execution; a schema-valid row can still fail later if assets are missing.

## Boundaries

- Do not assemble or launch model training commands here; route to `../training/`.
- Do not encode embeddings, run FAISS search, merge shards, or evaluate retrieval here; route to `../encoding-retrieval/`.
- Do not score reranker pairs or select reranker model arguments here; route to `../reranking/`.
- Do not execute multimodal or LLM retrievers here; only validate fields/assets and route execution to `../multimodal-llm/`.
