# UltraRAG Overview

## Purpose

Read this first when you need a compact, verified map of the repository.
It summarizes the package shape, core workflows, and the source roots that the
sub-skills cover.

## Verified package facts

- Distribution name: `ultrarag`
- Version: `0.3.0.2`
- Python support: `>=3.11, <3.13`
- CLI entry point: `ultrarag = ultrarag.client:main`
- Main execution layer: `src/ultrarag/client.py`
- MCP server wrapper: `src/ultrarag/server.py`
- Python API wrappers: `src/ultrarag/api.py`
- UI backend: `ui/backend`
- Example pipelines: `examples/demos/` and `examples/experiments/`

## Core execution model

UltraRAG uses YAML pipelines to orchestrate independent MCP servers.
A pipeline file declares:

- `servers:` — server name to server directory or path
- `pipeline:` — ordered steps, including plain steps, step remaps, loops, and
  branches

The build/run split is important:

- `ultrarag build <pipeline.yaml>` materializes generated parameter and server
  config files under `parameter/` and `server/` next to the pipeline file.
- `ultrarag run <pipeline.yaml> [--param <parameter.yaml>]` loads the generated
  configs and executes the pipeline.
- `ultrarag show ui` starts the Flask UI.
- `ultrarag show case` launches the case-study viewer for memory JSON.

## Verified public APIs

### `src/ultrarag/client.py`

- `build(config_path: str) -> None`
- `load_pipeline_context(config_path: str, param_path: Path | str | None = None)`
- `create_mcp_client(mcp_cfg: Dict[str, Any])`
- `execute_pipeline(client, context, is_demo=False, return_all=False, ...)`
- `run(config_path: str, param_path: Path | str | None = None, return_all=False, is_demo=False)`
- `main() -> None`
- `launch_ui(host='127.0.0.1', port=5050) -> None`
- `launch_case_study(config_path=None, host='127.0.0.1', port=8080) -> None`

### `src/ultrarag/api.py`

- `initialize(servers: List[str], server_root: str, log_level='info')`
- `ToolCall.<server>.<tool>(...)`
- `PipelineCall(pipeline_file, parameter_file, log_level='error')`

### `src/ultrarag/server.py`

- `UltraRAG_MCP_Server` extends FastMCP and captures tool/prompt metadata for
  build-time config generation.

## Repository map

| Area | Key paths | What it owns |
| --- | --- | --- |
| Orchestration | `src/ultrarag/client.py`, `src/ultrarag/api.py`, `examples/` | Build/run/show, YAML pipelines, loops, branches, demo workflows |
| Server contracts | `servers/` | MCP tools/prompts, parameter schemas, optional backends |
| UI and storage | `ui/backend`, `ui/frontend` | Flask app, auth, chat, KB, memory sync, frontend assets |
| Helper scripts | `script/` | Standalone deployment and inspection helpers |
| Documentation | `docs/`, `README.md` | Human-facing install and workflow explanations |

## Source-evidenced example families worth remembering

These labels identify the source evidence that informed the skill. Use the
bundled references and scripts here for runtime guidance instead of depending on
those source files being open.

- `examples/experiments/sayhello.yaml` — minimal install and CLI smoke check.
- `examples/demos/LLM*.yaml` — prompt/generation flows with and without memory.
- `examples/demos/RAG*.yaml` and `examples/experiments/rag_*.yaml` — retriever +
  generation pipelines.
- `examples/experiments/build_*.yaml`, `corpus_*.yaml`, `bm25_*.yaml`,
  `milvus_index.yaml` — corpus/index workflows.
- `examples/experiments/eval_trec*.yaml`, `evaluate_results.yaml` — evaluation.
- `examples/demos/LightResearch.yaml`, `AgentCPM-Report*.yaml`, `webnote*.yaml`,
  `search_*.yaml`, `rankcot.yaml`, `ircot.yaml` — iterative reasoning and
  report-style pipelines.
- `examples/experiments/visrag.yaml`, `multimodal_rag.yaml`, `vanilla_vlm.yaml` —
  multimodal workflows.

## When to read another file

- Read `references/troubleshooting.md` when an install, import, or runtime error
  needs a concrete recovery path.
- Read `sub-skills/pipelines/references/workflows.md` when you need a pipeline
  recipe or a starting point for a specific example family.
- Read `sub-skills/servers/references/backends-and-config.md` when choosing a
  backend, extra, or optional dependency set.
- Read `sub-skills/ui-and-storage/references/storage-auth.md` when the task is
  about users, sessions, KB storage, or filesystem layout.
