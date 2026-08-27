---
name: text2vec
description: "Operate text2vec for text embeddings, similarity search, model
  fine-tuning, evaluation, and serving without reopening the source repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# text2vec

Use this repo skill when a task involves the `text2vec` Python package, Chinese or multilingual sentence embeddings, text similarity, BM25 fallback retrieval, CoSENT/Sentence-BERT/BGE fine-tuning, or text2vec service templates.

## First checks

1. Install a compatible PyTorch build before expecting public model APIs to import.
2. Install `text2vec` and run a no-download import check:

```bash
python -c "from text2vec import SentenceModel, Similarity, BM25; print('text2vec ok')"
text2vec -h
```

3. For a safer environment probe, run the bundled helper from this skill:

```bash
python scripts/check_text2vec_env.py
```

Read [references/installation.md](references/installation.md) for optional dependency and backend decisions. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, model download, CUDA, data, CLI, and service failures.

## Route by task

| User task | Read |
|---|---|
| Generate sentence embeddings, use `SentenceModel`, run the `text2vec` CLI, choose `EncoderType`, preserve batch output rows, use Word2Vec, or understand NGram caveats | [sub-skills/embeddings/SKILL.md](sub-skills/embeddings/SKILL.md) |
| Score sentence pairs, use `Similarity`, call `cos_sim` / `semantic_search`, run dense top-k retrieval, or use BM25 as a no-network lexical fallback | [sub-skills/similarity-search/SKILL.md](sub-skills/similarity-search/SKILL.md) |
| Validate fine-tuning data, construct CoSENT/Sentence-BERT/BERT-match/BGE training commands, understand `train_model` parameters, or handle multi-GPU/bf16 training boundaries | [sub-skills/training-finetuning/SKILL.md](sub-skills/training-finetuning/SKILL.md) |
| Choose among released models, interpret Spearman/QPS tables, summarize local score files, or plan MTEB/C-MTEB-style evaluation without running large downloads by default | [sub-skills/evaluation-benchmarks/SKILL.md](sub-skills/evaluation-benchmarks/SKILL.md) |
| Build a FastAPI endpoint, compare FastAPI/Jina/Gradio service patterns, or avoid blocking forever-server verification | [sub-skills/serving-deployment/SKILL.md](sub-skills/serving-deployment/SKILL.md) |

## Package surface at a glance

- Main import: `import text2vec`.
- Important inference APIs: `SentenceModel`, `SBert`, `EncoderType`, `Word2Vec`, `BM25`, `Similarity`, `SimilarityType`, `EmbeddingType`, `cos_sim`, `semantic_search`.
- Training APIs: `CosentModel`, `SentenceBertModel`, `BertMatchModel`, `BgeModel`, plus text-matching and BGE dataset loaders.
- CLI entry point: `text2vec`, with required `--input_file` and optional `--output_file`, `--model_type`, `--model_name`, `--encoder_type`, `--batch_size`, `--max_seq_length`, `--chunk_size`, `--device`, `--show_progress_bar`, `--normalize_embeddings`, and `--multi_gpu`.
- Default neural model names usually require Hugging Face access unless cached. Prefer a local HF-compatible model directory for offline smoke tests.
- Word2Vec requires `gensim` and either a local vector file or the built-in Tencent lightweight vector download.

## Bundled root files

- [references/installation.md](references/installation.md): public install variants, required `torch` note, optional dependencies, backend choices, and environment checks.
- [references/troubleshooting.md](references/troubleshooting.md): cross-skill failure modes and recovery steps.
- [references/repo-provenance.md](references/repo-provenance.md): source snapshot used to create this skill; read before refresh decisions.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured router metadata for managed repo-skill import.
- [scripts/check_text2vec_env.py](scripts/check_text2vec_env.py): no-download diagnostic helper for imports, optional deps, torch backend, BM25, `cos_sim`, and `semantic_search`.

## Operating rules

- Do not run default model downloads, full training, benchmarks, JinaHub fetches, Gradio launches, or long-lived servers unless the user explicitly approves network/runtime side effects.
- Do not use synthetic CPU smoke checks as proof of CUDA, bf16, multi-GPU, or production-scale training coverage.
- Prefer bundled validators and helpers before expensive commands: data validation before training, no-network BM25 before dense retrieval when embeddings are absent, and local model directories before default downloads.
- For stale-source decisions, compare the current checkout against [references/repo-provenance.md](references/repo-provenance.md) and refresh if APIs, docs, examples, tests, or package metadata changed.
