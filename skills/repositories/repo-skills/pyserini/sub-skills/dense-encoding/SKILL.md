---
name: dense-encoding
description: "Use Pyserini dense encoders, Faiss search, Lucene dense/HNSW
  routing, hybrid retrieval, and dense backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dense Encoding

Use this sub-skill when a task involves encoding corpora or queries, choosing dense encoder classes, searching Faiss indexes, searching Lucene dense/HNSW indexes, combining dense and sparse retrieval, selecting CPU/GPU backends, using OpenAI embeddings, or diagnosing missing `faiss` and model-backend failures.

## Route First

- Send Python, Java, package installation, optional dependency installation, and broad runtime checks to `../install-and-runtime/SKILL.md`.
- Send Lucene sparse/impact indexing, local Lucene HNSW index construction, analyzers, query builders, index readers, and document fetching details to `../index-search-fetch/SKILL.md`.
- Send qrels, run evaluation, run conversion, interpolation, and fusion-result scoring to `../evaluation-and-fusion/SKILL.md`.
- Send REST/MCP dense index aliases and server configuration to `../serving-and-agent-tools/SKILL.md`.

## Default Workflow

1. Validate dense input files with `scripts/validate_dense_jsonl.py` before any model command.
2. Choose an encoder/backend from `references/model-and-backend-reference.md`; prefer `--device cpu` unless GPU availability is confirmed.
3. Build commands with `scripts/dense_cli_builder.py` and review the printed command before running it.
4. For corpus encoding, use `python -m pyserini.encode` with `input`, `output`, and `encoder` subcommands.
5. For Faiss retrieval, either encode directly with `output --to-faiss` or build a Faiss index from encoded JSONL, then search with `python -m pyserini.search.faiss`.
6. For Lucene dense retrieval, search with `python -m pyserini.search.lucene --dense --hnsw` or `--flat`; route index-building details to `index-search-fetch`.
7. For hybrid retrieval, pair a `FaissSearcher` with a sparse Lucene searcher and tune fusion parameters; route final run evaluation to `evaluation-and-fusion`.

## References

- `references/encoding-and-dense-search.md` covers JSONL schemas, encoding, Faiss indexing/search, Lucene dense search, and hybrid retrieval.
- `references/model-and-backend-reference.md` maps encoder classes, devices, OpenAI, multimodal, UniIR, and encoded-query choices.
- `references/troubleshooting.md` covers missing `faiss`, Torch CPU/CUDA mismatch, model downloads, OpenAI keys, JSONL field errors, dimension mismatches, and hybrid alignment failures.

## Safety Defaults

- Do not run model commands until the user has confirmed model downloads, local model paths, cached weights, or OpenAI credentials as appropriate.
- Do not assume Faiss indexes store raw document text; use a companion Lucene index for content fetch workflows.
- Do not assume Faiss GPU support from `faiss-cpu`; use CPU defaults unless a compatible GPU build is available.
