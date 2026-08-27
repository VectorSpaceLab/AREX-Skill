# Installation and Dependencies

## Purpose

Read this when choosing how to install, inspect, or troubleshoot CrewAI packages. This reference distills package metadata from the CrewAI workspace and live inspection of package version `1.14.8a2`.

## Packages

| Distribution | Import name | Role |
| --- | --- | --- |
| `crewai` | `crewai` | Main runtime package for agents, tasks, crews, flows, memory, knowledge, RAG, LLMs, MCP, skills, telemetry, and security. |
| `crewai-cli` | `crewai_cli` | `crewai` console entry point and project/deploy/train/test/run commands. |
| `crewai-tools` | `crewai_tools` | Official tool exports, adapters, RAG loaders, MCP/Zapier/enterprise adapters, and integration tools. |
| `crewai-files` | `crewai_files` | File input resolution, multimodal formatting, provider constraints, upload cache, and file processing. |
| `crewai-core` | `crewai_core` | Shared auth, token, paths, settings, telemetry, printer, lock-store, and version utilities. |
| `crewai-devtools` | `crewai_devtools` | Maintainer docs/release helpers for this monorepo, not a normal user runtime dependency. |

## Python and Base Install

- The workspace declares `requires-python = ">=3.10,<3.14"`.
- Use Python 3.11 or 3.12 for broadest binary-wheel compatibility when inspecting or developing CrewAI locally.
- For normal users, `pip install crewai` installs the main runtime and CLI entry point.
- Install `crewai-tools` only when official tools are needed; many tool integrations also need API keys or optional third-party packages.
- Avoid installing every optional extra by default. Choose extras from the actual workflow: LLM provider, files, RAG/vector store, tools, deploy, or hosted integrations.

## Important Optional Areas

- `crewai[tools]` pulls `crewai-tools` when the user wants official tools alongside the runtime.
- RAG and memory can require vector-store packages such as ChromaDB, LanceDB, Qdrant, or backend-specific embedding dependencies.
- `crewai-files` needs binary packages for PDFs, images, audio/video, and MIME detection; document/video processing failures are usually optional-dependency or system-library issues.
- Hosted CrewAI AMP/deploy/organization/triggers commands require authentication and network access. Treat them as credential-bound, not safe local smoke tests.
- Web/search/database/cloud tools normally require service credentials and should not be instantiated against live services just to inspect configuration.

## Verified Local Facts

Live package inspection verified these public surfaces for version `1.14.8a2`:

- `crewai`, `crewai_cli`, `crewai_tools`, `crewai_files`, `crewai_core`, and `crewai_devtools` import successfully in a private inspection environment.
- `crewai` exports public runtime classes including `Agent`, `Task`, `Crew`, `Flow`, `LLM`, `Process`, `CrewOutput`, `TaskOutput`, `Knowledge`, `CheckpointConfig`, `BaseTool`, and `CrewStructuredTool`.
- `Process` values are `sequential` and `hierarchical`.
- The CLI command group includes `create`, `run`, `train`, `test`, `replay`, `chat`, `deploy`, `flow`, `checkpoint`, `memory`, `reset-memories`, `tool`, `template`, `traces`, `uv`, and auth/organization/enterprise commands.

## Safe Install Checks

Use local checks that do not call LLMs, tools, or hosted services:

```bash
python - <<'PY'
import crewai, crewai_cli, crewai_tools, crewai_files
print(crewai.__version__)
PY

crewai --help
python -m pip check
```

For a bundled diagnostic that reports import and CLI status without executing workflows, run:

```bash
python scripts/check_crewai_environment.py --json
```

## Dependency Pitfalls

- Dependency resolvers may choose newer transitive packages than CrewAI pins. If `pip check` reports OpenTelemetry or Pillow conflicts, align package versions with CrewAI package metadata before trusting runtime inspection.
- Large binary wheels such as vector stores, PDF/image processing, ONNX/runtime packages, and audio/video packages can be slow to install. Install them only for workflows that need them.
- Use package-specific official indexes for accelerator or backend packages; do not swap CUDA/torch-style indexes to a generic mirror unless it is known to host the required wheels.
- A successful install is not enough for skill or app validation. Verify metadata, imports, `pip check`, and at least CLI help or safe import diagnostics.
