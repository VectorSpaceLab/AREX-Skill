---
name: knowledge-storm
description: "Operate the knowledge-storm/STORM package for Wikipedia-style
  article generation, corpus-grounded VectorRM/Qdrant workflows, and
  collaborative Co-STORM knowledge curation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# knowledge-storm

Use this repo skill when the task names STORM, Co-STORM, `knowledge-storm`, `knowledge_storm`, `STORMWikiRunner`, `CoStormRunner`, `VectorRM`, `QdrantVectorStoreManager`, or asks for package-specific long-form knowledge curation with retrieval and LiteLLM-backed models.

## Route by task

- **STORM Wikipedia-like article generation**: use `sub-skills/storm-wiki/SKILL.md` for `STORMWikiRunner`, `STORMWikiLMConfigs`, staged research/outline/article/polish runs, internet retrievers, callbacks, output inspection, and demo-light setup notes.
- **User corpus or vector-store grounding**: use `sub-skills/vector-corpus/SKILL.md` for CSV validation, Kaggle arXiv conversion, Qdrant offline/online stores, `VectorRM`, `QdrantVectorStoreManager`, embedding devices, and corpus-grounded STORM runs.
- **Collaborative Co-STORM**: use `sub-skills/co-storm/SKILL.md` for `CollaborativeStormLMConfigs`, `RunnerArgument`, `CoStormRunner`, `warm_start`, `step`, mind-map state, logging, report generation, and turn-policy troubleshooting.
- **Package-wide setup and environment checks**: use the root references below and `scripts/check_knowledge_storm_runtime.py` before choosing a full workflow.

## Fast start

1. Install the public package in a Python 3.10+ environment: `pip install knowledge-storm`.
2. Run `python scripts/check_knowledge_storm_runtime.py --json` to check imports, package/distribution versions, optional packages, retriever environment variables, and CUDA visibility.
3. Pick the sub-skill that owns the workflow and run its bundled helper with `--help` and `--dry-run` before any network, model, search, embedding, or Qdrant work.
4. Keep model, embedding, search, Qdrant, and output directories explicit. Most real runs need provider keys, web access, and enough quota for multi-step retrieval/LLM calls.

## Root references

- `references/package-overview.md` summarizes the installed package, major APIs, selected workflows, and sub-skill boundaries.
- `references/configuration-and-secrets.md` maps model, embedding, retriever, VectorRM, Qdrant, and secrets settings.
- `references/troubleshooting.md` covers cross-cutting install/import, optional dependency, credential, version, output, and cost failures.
- `references/repo-provenance.md` records source revision, package version evidence, selected source paths, and known extraction limits.
- `references/repo-routing-metadata.json` provides structured router placement for import tooling.

## Avoid

- Do not use this skill for generic RAG, generic Qdrant, generic LiteLLM, or generic article-writing tasks unless the STORM package is the orchestrating framework.
- Do not run full STORM or Co-STORM workflows without checking credentials, retriever access, and cost/rate-limit knobs first.
- Do not assume CUDA is required. Core STORM and Co-STORM are model/search/credential-bound; CPU is sufficient for package operation, while CUDA/MPS can accelerate local embedding models used by VectorRM.
- Do not depend on the original repository checkout. Use the bundled references and scripts in this skill tree.
