---
name: pruning-export-evaluation
description: "Export SPLADE vectors for Anserini, prune Anserini-style JSONL,
  and plan BEIR/PISA evaluation without unsafe external downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SPLADE Pruning, Export, and Evaluation

Use this sub-skill when the task involves Anserini export files, static pruning of SPLADE JSONL vectors, BEIR evaluation planning, PISA evaluation planning, or optional external evaluation dependencies.

## Read First

- [references/export-evaluation.md](references/export-evaluation.md): `splade.create_anserini`, `EncodeAnserini` formats, BEIR/PISA planning, and external engine boundaries.
- [references/pruning-workflows.md](references/pruning-workflows.md): safe static pruning workflows, bundled script usage, and why upstream shell workflows are reference-only.
- [references/troubleshooting.md](references/troubleshooting.md): quantization, empty vectors, BEIR downloads, Java/Pyserini/Anserini, PISA, and `pytrec_eval` failures.

## Route Tasks

- Use this sub-skill for `python -m splade.create_anserini`, `docs_anserini.jsonl`, `queries_anserini.tsv`, pruning, BEIR, PISA, Pyserini/Anserini, and TREC metric dependency questions.
- Route core SPLADE training, indexing, retrieval, Hydra package selection, and toy/full pipeline commands to `../hydra-pipelines/SKILL.md`.
- Route model classes, data loaders, raw/qrel schemas, vector semantics, and API smoke checks to `../model-data-api/SKILL.md`.
- Route HuggingFace Trainer training or reranking workflows to `../hf-training-reranking/SKILL.md`.

## Safe Actions

- Generate export command templates with `python -m splade.create_anserini`; do not assume Anserini or PISA is installed.
- Use `scripts/prune_doc_index.py` for local top-k or value-threshold pruning of Anserini-style document JSONL.
- Use `scripts/prune_quantile.py` for local per-token quantile pruning of Anserini-style document JSONL.
- Use `--dry-run` and `--limit` before writing large pruned collections.
- Treat BEIR, Anserini, Pyserini, PISA, and metric evaluation as explicit external-prerequisite workflows that may require downloads, Java, compiled binaries, or network access.

## Avoid

- Do not run BEIR downloads, Pyserini indexing/search, Anserini regressions, PISA binaries, or large benchmark workflows unless the user explicitly approves external engines, downloads, and runtime cost.
- Do not point runtime instructions at the original repository shell scripts; use the bundled Python pruning scripts and the references in this sub-skill.
- Do not treat pruning output as fully evaluated retrieval quality until an external index/search/evaluation stack has been prepared and run intentionally.
