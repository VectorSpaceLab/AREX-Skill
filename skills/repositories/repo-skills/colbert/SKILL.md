---
name: colbert
description: "Use ColBERT/colbert-ai for late-interaction retrieval: prepare
  data, inspect configs, train/fine-tune, index collections, search rankings,
  update indexes, serve search, evaluate MS MARCO/LoTTE outputs, or reason about
  Baleen multi-hop retrieval."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColBERT Repo Skill

Use this skill when a task involves the `colbert-ai` Python package, the ColBERTv2/PLAID retrieval workflow, ColBERT data formats, or the optional Baleen multi-hop extension.

ColBERT is a late-interaction neural retrieval system. Typical workflows prepare TSV data, choose or train a checkpoint, build an index, search queries, save rankings, and evaluate retrieval quality.

## Start Here

1. Install the public package with the needed backend, for example `pip install "colbert-ai[torch,faiss-cpu]"` for CPU-oriented inspection or `pip install "colbert-ai[torch,faiss-gpu]"` when CUDA/FAISS GPU is available and intended.
2. Run `python scripts/check_colbert_env.py` to verify imports, package versions, `torch`/CUDA visibility, and important public API signatures.
3. Read `references/troubleshooting.md` if imports fail, FAISS/Torch extras are missing, CUDA is unavailable, or old `torch`/`setuptools` stacks report `pkg_resources` errors.
4. Read `references/repo-provenance.md` before deciding whether this generated skill matches a current checkout or should be refreshed.

## Route Tasks

- Use `sub-skills/data-and-evaluation/` for `collection.tsv`, `queries.tsv`, rankings, qrels, LoTTE layouts, preprocessing, validation, and metric evaluation.
- Use `sub-skills/modeling-and-tokenization/` for `Checkpoint`, `ColBERTConfig`, tokenizer behavior, marker tokens, max lengths, dimensions, and safe model/config inspection.
- Use `sub-skills/training-and-distillation/` for `Trainer`, triples/examples JSONL, ColBERTv1/v2-style fine-tuning, distillation/scored examples, and GPU/resource planning.
- Use `sub-skills/indexing-and-search/` for `Indexer`, `Searcher`, `RunConfig`, index roots, single-query or batch search, ranking save behavior, and search tuning.
- Use `sub-skills/index-updates-and-serving/` for `IndexUpdater`, add/remove/persist workflows, coalescing updated artifacts, and lightweight JSON search serving.
- Use `sub-skills/baleen-multihop/` for optional Baleen `HopSearcher`, `Condenser`, `collectionX`, multi-hop retrieval plans, and static diagnostics.

## Verified Package Facts

- Distribution name: `colbert-ai`; import package: `colbert`; generated against package version `0.2.22`.
- Public imports verified during creation: `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.
- Important public constructors: `Indexer(checkpoint, config=None, verbose=3)`, `Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)`, `Trainer(triples, queries, collection, config=None)`, and `IndexUpdater(config, searcher, checkpoint=None)`.
- CPU imports and validation helpers are safe for inspection; practical indexing, training, updating, and full Baleen runs often need local checkpoints, indexes, datasets, and CUDA/GPU resources.

## Core Workflow

1. Validate data with the data/evaluation sub-skill before starting expensive indexing or training.
2. Inspect checkpoint/config/tokenization assumptions with the modeling sub-skill when changing `query_maxlen`, `doc_maxlen`, `dim`, marker tokens, or checkpoint sources.
3. Train or fine-tune only after validating triples/examples and planning GPU resources.
4. Index with explicit `RunConfig(root=..., experiment=...)`, `ColBERTConfig(...)`, checkpoint, index name, and overwrite/resume policy.
5. Search with the same root/experiment/index naming assumptions or pass explicit `index_root`; save rankings with an explicit output path when possible.
6. Treat mutable index updates and serving as operations on an existing index; back up artifacts before `persist_to_disk()`.

## Bundled Root Files

- `references/repo-provenance.md` records the source repository snapshot, package version, evidence paths, and refresh checks.
- `references/troubleshooting.md` covers cross-cutting install/import/backend/package issues shared by all sub-skills.
- `scripts/check_colbert_env.py` performs a deterministic environment and public-signature inspection without loading checkpoints, downloading models, or running retrieval.

## Safety Boundaries

- Do not assume a successful import means a user has working checkpoints, indexes, datasets, FAISS GPU, or CUDA.
- Do not start long training, indexing, Hugging Face downloads, benchmark evaluation, or server processes unless the user explicitly wants that side effect.
- Do not mutate an existing index with `IndexUpdater.persist_to_disk()` until the target index is backed up or disposable.
- Prefer bundled validation/template scripts in this skill over copying commands from old notebooks or generated docs.
