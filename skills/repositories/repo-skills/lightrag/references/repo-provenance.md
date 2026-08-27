# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a LightRAG checkout. If the current repo commit, dirty state, package version, optional dependency layout, or major evidence paths differ from this snapshot, run a repo-skill refresh before relying on implementation details.

## Snapshot

schema: `disco.repo-provenance.v1`

| Field | Value |
| --- | --- |
| Source project | LightRAG |
| Distribution | `lightrag-hku` |
| Package version inspected | `1.5.4` |
| Import root | `lightrag` |
| Source commit | `4e1f95269b32cd803cb96e0acc24d922aa6b6932` |
| Source branch | `main` |
| Exact tag | none |
| Remote URL | `https://github.com/HKUDS/LightRAG` |
| Working tree state at generation | dirty: generated `skills/` artifacts were untracked |
| Python support | `>=3.10` from package metadata |
| Environment evidence | private inspection environment verified `lightrag-hku[api]`; local paths are intentionally omitted |

## Evidence Paths

These paths are relative to the LightRAG repository root and were used as source evidence. They are recorded for staleness checks only; runtime skill instructions are self-contained and do not require opening these files.

- `pyproject.toml`
- `setup.py`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/ProgramingWithCore.md`
- `docs/FileProcessingPipeline.md`
- `docs/ThirdPartyParser.md`
- `docs/ParserDebugCLI.md`
- `docs/ParagraphSemanticChunking.md`
- `docs/LightRAGSidecarFormat.md`
- `docs/LightRAG-API-Server.md`
- `docs/InteractiveSetup.md`
- `docs/DockerDeployment.md`
- `docs/FrontendBuildGuide.md`
- `docs/RoleSpecificLLMConfiguration.md`
- `docs/AsymmetricEmbedding.md`
- `docs/MilvusConfigurationGuide.md`
- `docs/OfflineDeployment.md`
- `lightrag/`
- `lightrag/api/`
- `lightrag/kg/`
- `lightrag/llm/`
- `lightrag/parser/`
- `lightrag/chunker/`
- `lightrag/sidecar/`
- `lightrag/tools/`
- `lightrag_webui/`
- `examples/`
- `reproduce/`
- `scripts/test.sh`
- `scripts/setup/`
- `tests/`
- `env.example`
- `config.ini.example`

## Installed Package Facts Verified

- `lightrag` imports from the `lightrag-hku` distribution.
- Public objects inspected include `LightRAG`, `QueryParam`, `EmbeddingFunc`, `wrap_embedding_func_with_attrs`, `RoleLLMConfig`, parser routing helpers, chunker exports, API route factories, and the storage backend registry.
- Console entry points from package metadata include `lightrag-server`, `lightrag-gunicorn`, `lightrag-hash-password`, `lightrag-download-cache`, `lightrag-clean-llmqc`, and `lightrag-rebuild-vdb`.
- Optional dependency groups discovered include `api`, `offline-storage`, `offline-llm`, `offline`, `test`, `evaluation`, and `observability`.

## Refresh Triggers

Refresh this skill if any of the following change materially:

- `LightRAG` or `QueryParam` signatures, lifecycle requirements, or query modes.
- Parser routing names, process-option letters, chunking strategy contracts, or pipeline concurrency fields.
- Storage backend registry class names, workspace rules, migrations, or operational tool entry points.
- LLM role ids, `RoleLLMConfig`, provider modules, asymmetric embedding behavior, rerank configuration, or cache identity rules.
- API route factories, auth/JWT behavior, setup wizard outputs, WebUI package scripts, or console entry points.
- Package optional extras, Python version constraints, or runtime dependency grouping.
