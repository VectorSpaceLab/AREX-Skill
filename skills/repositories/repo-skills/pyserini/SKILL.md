---
name: pyserini
description: "Use Pyserini for reproducible information retrieval:
  install/runtime setup, Lucene indexing/search/fetch, dense encoding/Faiss,
  evaluation/fusion, REST/MCP serving, and source checkout maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pyserini Repo Skill

## Purpose

Use this skill when the user asks about Pyserini, Anserini-backed Lucene retrieval, Pyserini dense/Faiss retrieval, Pyserini evaluation/fusion tools, REST or MCP servers, or maintaining a Pyserini source checkout.

Pyserini is a Python toolkit for reproducible information retrieval research with sparse and dense representations. It wraps Anserini/Lucene for sparse and some dense retrieval, uses Faiss for dense vector search when that optional package is installed, and includes run evaluation, fusion, reproducibility, REST, and MCP server surfaces.

## Start Here

1. If the task mentions installation, imports, Java, PyJNIus, Faiss, Torch, CUDA, package resources, or `pip check`, read `sub-skills/install-and-runtime/SKILL.md`.
2. If the task mentions Lucene indexing, BM25/search, fetching documents, analyzers, query builders, collections, or index readers, read `sub-skills/index-search-fetch/SKILL.md`.
3. If the task mentions embeddings, encoders, Faiss, dense indexes, Lucene dense/HNSW, hybrid retrieval, OpenAI/Hugging Face models, GPU/CPU devices, or multimodal retrieval, read `sub-skills/dense-encoding/SKILL.md`.
4. If the task mentions TREC/MS MARCO/KILT runs, qrels, metrics, `trec_eval`, run conversion, RRF, interpolation, fusion, or two-click reproducibility matrices, read `sub-skills/evaluation-and-fusion/SKILL.md`.
5. If the task mentions REST API, FastAPI, OpenAPI, MCP, `mcpyserini`, server YAML config, API keys, cache, load shedding, Claude Desktop, Cursor, or agent tools, read `sub-skills/serving-and-agent-tools/SKILL.md`.
6. If the task is about contributing to the Pyserini source checkout, building source resources, initializing submodules, selecting safe tests, or avoiding heavyweight native validation, read `sub-skills/repo-development/SKILL.md`.

## Minimal Runtime Checks

For a user environment, start with the root wrapper:

```bash
python scripts/check_pyserini_install.py --help
python scripts/check_pyserini_install.py --json
python scripts/check_pyserini_install.py --check-lucene --check-faiss --check-server
```

The wrapper delegates to `sub-skills/install-and-runtime/scripts/check_pyserini_runtime.py` and reports missing Python packages, Java/JVM issues, Faiss availability, REST/MCP import readiness, and dependency conflicts without downloading indexes or models.

## Install Baseline

For normal usage:

```bash
pip install pyserini
```

Pyserini 2.3.0 declares Python `>=3.12` and expects Java 21 for Anserini/Lucene-backed workflows. Dense retrieval often needs Torch/Transformers/ONNX Runtime, and Faiss must be installed separately as `faiss-cpu` or a platform-appropriate GPU variant. Multimodal support uses the optional Pyserini extra.

For source checkout development, do not assume `pip install -e .` is enough for Lucene-backed imports. Source workflows may need the `tools` submodule, native evaluation tools, and an Anserini fatjar resource; route those tasks to `sub-skills/repo-development/SKILL.md`.

## Capability Map

Read `references/public-capabilities.md` for a compact map of Pyserini APIs, CLIs, data formats, optional dependencies, and native verification candidates.

Read `references/troubleshooting.md` for cross-cutting install/import/runtime failures before drilling into a sub-skill-specific troubleshooting file.

Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout. If the current commit, dirty state, package metadata, Java/resource behavior, or major evidence paths differ, refresh the skill.

## Routing Rules

- Prefer `index-search-fetch` for raw document access because Faiss indexes usually do not store raw document text.
- Prefer `dense-encoding` for model selection and Faiss command construction, but route runtime dependency installation to `install-and-runtime`.
- Prefer `evaluation-and-fusion` after retrieval has produced a run file; do not bury qrels or metrics inside search guidance.
- Prefer `serving-and-agent-tools` when a user wants an HTTP/MCP interface over existing indexes; do not re-explain Lucene scoring there unless the task is server-specific.
- Prefer `repo-development` only for maintaining the source checkout. Normal Pyserini users should not run broad repo scripts, integration manifests, or experiment launchers by default.

## Safety Defaults

- Do not download prebuilt indexes, model checkpoints, benchmark corpora, or experiment assets unless the user explicitly asks or confirms.
- Do not run broad native test suites, two-click reproduction matrices, or job manifests before generating/using the targeted guidance.
- Do not expose local environment paths, tokens, cache paths, or private index paths in reusable answers.
- Use bundled scripts in this skill tree for validation and command construction before running Pyserini commands that can download data or start Java/server processes.
