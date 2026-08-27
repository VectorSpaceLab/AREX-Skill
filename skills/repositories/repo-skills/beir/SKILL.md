---
name: beir
description: "Route BEIR repository tasks for benchmark data loading, retrieval
  evaluation, reranking, generation, and training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BEIR Repo Skill

Use this skill for BEIR, the Python benchmark framework for information retrieval datasets, retrievers, rerankers, query generation, and SentenceTransformers-style training.

## First Checks

- Install the public package with `pip install beir`, or use an editable install only when working on a checkout.
- Verify the core import with `python -c "import beir; print(beir.__all__)"`.
- Run `python scripts/check_beir_environment.py` to inspect core and optional dependencies without contacting external services.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.
- Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, optional backend, data, service, credential, and scale failures.

## Route by Task

- Use [data-loading](sub-skills/data-loading/SKILL.md) for BEIR `corpus.jsonl`, `queries.jsonl`, `qrels/<split>.tsv`, Hugging Face datasets, local validation, downloads, runfiles, and result JSON persistence.
- Use [retrieval-evaluation](sub-skills/retrieval-evaluation/SKILL.md) for `EvaluateRetrieval`, dense exact search, FAISS, sparse retrieval, BM25/Elasticsearch, API embeddings, custom model protocols, metrics, embedding caches, and runfile export.
- Use [reranking](sub-skills/reranking/SKILL.md) when first-stage retrieval results need a cross-encoder, MonoT5, SBERT, or custom pair-scoring second stage.
- Use [generation](sub-skills/generation/SKILL.md) for synthetic query generation, generated qrels, passage expansion, output prefixes, and fake-model smoke checks.
- Use [training](sub-skills/training/SKILL.md) for `TrainRetriever`, pair/triplet construction, IR evaluators, BEIR losses, hard-negative workflows, and safe training-run planning.

## Common Workflow Order

1. Start in `data-loading` to validate local files or understand remote dataset requirements.
2. Move to `retrieval-evaluation` to choose a backend and compute BEIR metrics.
3. Add `reranking` only after you have candidate `results` from a first-stage retriever.
4. Use `generation` when you need generated queries, qrels, or expanded corpora before retrieval or training.
5. Use `training` when preparing model fine-tuning data or planning a long SentenceTransformers run.

## Bundled Smoke Tests

Run these from inside the `skills/beir/` directory or pass the full script paths from elsewhere:

```bash
python scripts/check_beir_environment.py
python sub-skills/data-loading/scripts/make_tiny_beir_dataset.py /tmp/beir-tiny
python sub-skills/data-loading/scripts/validate_beir_dataset.py /tmp/beir-tiny --split test
python sub-skills/retrieval-evaluation/scripts/retrieval_smoke.py
python sub-skills/reranking/scripts/rerank_smoke.py
python sub-skills/generation/scripts/generation_smoke.py
python sub-skills/training/scripts/training_data_smoke.py --exercise-max-corpus-error
```

These checks are offline and deterministic. They do not download BEIR datasets, model weights, or contact Elasticsearch/API services.

## Dependency Boundaries

- Core BEIR data loading and metric evaluation need the package runtime dependencies from `pyproject.toml`.
- FAISS workflows require `faiss-cpu` or a compatible GPU FAISS installation.
- BM25 workflows require the `elasticsearch` extra and a running Elasticsearch-compatible service; installing the Python package alone is not enough.
- Cohere and Voyage API embedding workflows require provider packages, environment variables, network access, and account credentials.
- vLLM, LoRA, NVEmbed, LLM2Vec, PEFT, TILDE, MonoT5, and full training workflows can require large model downloads, GPU memory, and careful PyTorch/Transformers compatibility.

## Refresh Guidance

Refresh this skill if BEIR package metadata, public APIs, examples, optional dependency names, supported Python versions, retrieval model wrappers, generation wrappers, or training helpers change. The provenance file records the source commit and evidence paths used to generate this version.
