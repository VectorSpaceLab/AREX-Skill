# CrewAI Troubleshooting

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: chromadb`, `lancedb`, `qdrant_client`, or embedding package | Memory/RAG/vector-store dependency missing | Read `sub-skills/memory-knowledge-and-rag/references/embedding-and-storage.md`; install only the backend needed for the selected storage/provider. |
| `ModuleNotFoundError` for `pymupdf`, `av`, `python_magic`, `PIL`, or PDF/audio/video packages | File or multimodal optional dependency missing | Read `sub-skills/files-and-multimodal/references/troubleshooting.md`; run the file checker before attempting uploads or LLM calls. |
| `pip check` reports OpenTelemetry version conflicts | A transitive dependency upgraded OpenTelemetry beyond CrewAI pins | Reinstall the versions required by the CrewAI package metadata; verify `python -m pip check` before inspecting runtime behavior. |
| `pip check` reports Pillow/PDF conflicts | PDF tooling and `crewai-files` selected incompatible Pillow versions | Use package metadata constraints for the workflow. If PDF parsing is required, test the exact PDF path; otherwise avoid installing broad file extras. |
| Import works from the repo but distribution metadata is missing | Running from checkout path instead of installed package | Use an isolated environment and verify both `importlib.metadata.version("crewai")` and `import crewai`. |

## CLI and Project Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `crewai run` says no project or missing `pyproject.toml` | Command is not being run from a CrewAI project root | Use `sub-skills/cli-and-projects/scripts/inspect_crewai_cli.py --project-root <dir>` to check layout. |
| JSONC project prompts unexpectedly or placeholders remain unresolved | Missing `inputs` defaults or CLI input values | Read `sub-skills/core-runtime/references/jsonc-projects.md` and `sub-skills/cli-and-projects/references/troubleshooting.md`. |
| `crewai chat` fails before kickoff | `chat_llm` is not configured or provider credentials are missing | Configure `chat_llm` in `crew.jsonc` or classic `Crew(...)`; then validate provider requirements with `sub-skills/llm-and-providers/scripts/check_llm_config.py`. |
| `crewai deploy`, `login`, `org`, or trigger commands fail | Hosted CrewAI AMP credentials/network/organization configuration missing | Treat these as credential-bound. Do not use them as local smoke tests unless the user explicitly provides credentials and asks for hosted verification. |

## Runtime and Workflow Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Hierarchical crew errors about manager | `process="hierarchical"` without `manager_llm` or `manager_agent` | Use `core-runtime` troubleshooting and run the JSONC validator. |
| Task context points to a later task | Forward context reference in sequential task list | Reorder tasks or remove forward reference; run `sub-skills/core-runtime/scripts/validate_crew_definition.py`. |
| Flow listener never runs | Router emits unmatched label, listener typo, or wrong trigger | Run `sub-skills/flows-and-events/scripts/validate_flow_graph.py`; read flow troubleshooting. |
| Tool call fails with schema or result errors | Tool args schema mismatch or output not serializable | Read `sub-skills/tools-and-mcp/references/troubleshooting.md`; inspect tool schema before kickoff. |
| Missing or duplicate traces | Environment tracing settings conflict with crew/flow-level `tracing` or duplicate instrumentation | Run `sub-skills/observability-and-hooks/scripts/check_tracing_config.py` and read tracing troubleshooting. |

## Safety Boundaries

- Do not run untrusted CrewAI projects just to inspect them. JSONC `custom:<name>` tools and `{"python": "module.attribute"}` callbacks execute local Python.
- Do not run LLM-backed crews, web/search/database tools, hosted deploy/login flows, or MCP servers without user authorization and required credentials.
- Prefer the bundled static diagnostics before native examples/tests.
- For monorepo contribution tasks, use `sub-skills/repo-development` to choose focused checks and avoid forbidden docs snapshot/image edits.
