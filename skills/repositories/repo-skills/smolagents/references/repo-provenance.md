# Repo Provenance

- schema: `disco.repo-provenance.v1`

## Source Snapshot

- Source project: Hugging Face `smolagents`
- Package distribution: `smolagents`
- Package version inspected: `1.27.0.dev0`
- Git commit: `526069c1ead958b36d9fd09a6b1ef37f68ed6ade`
- Git branch: `main`
- Exact tag: none detected
- Working tree state: dirty at generation time because DisCo-generated `skills/` artifacts were being added during this run; no pre-existing source-code modifications were reported by the initial repository snapshot.
- Remote URL: https://github.com/huggingface/smolagents

## Evidence Paths

Runtime skill content was derived from these repository-relative evidence paths:

- `pyproject.toml`
- `README.md`
- `src/smolagents/__init__.py`
- `src/smolagents/agents.py`
- `src/smolagents/tools.py`
- `src/smolagents/default_tools.py`
- `src/smolagents/models.py`
- `src/smolagents/local_python_executor.py`
- `src/smolagents/remote_executors.py`
- `src/smolagents/cli.py`
- `src/smolagents/vision_web_browser.py`
- `src/smolagents/gradio_ui.py`
- `src/smolagents/mcp_client.py`
- `src/smolagents/memory.py`
- `src/smolagents/monitoring.py`
- `src/smolagents/serialization.py`
- `src/smolagents/tool_validation.py`
- `src/smolagents/prompts/`
- `docs/source/en/`
- `examples/agent_from_any_llm.py`
- `examples/gradio_ui.py`
- `examples/inspect_multiagent_run.py`
- `examples/multi_llm_agent.py`
- `examples/multiple_tools.py`
- `examples/plan_customization/`
- `examples/rag.py`
- `examples/rag_using_chromadb.py`
- `examples/sandboxed_execution.py`
- `examples/server/`
- `examples/structured_output_tool.py`
- `examples/text_to_sql.py`
- `tests/test_agents.py`
- `tests/test_cli.py`
- `tests/test_default_tools.py`
- `tests/test_gradio_ui.py`
- `tests/test_local_python_executor.py`
- `tests/test_mcp_client.py`
- `tests/test_memory.py`
- `tests/test_models.py`
- `tests/test_monitoring.py`
- `tests/test_remote_executors.py`
- `tests/test_search.py`
- `tests/test_serialization.py`
- `tests/test_tool_validation.py`
- `tests/test_tools.py`
- `tests/test_vision_web_browser.py`

## Exclusions and Refresh Signals

- Multilingual documentation under `docs/source/es`, `docs/source/hi`, `docs/source/ko`, and `docs/source/zh` was treated as duplicate localization evidence, not primary extraction input.
- `examples/open_deep_research/` was treated as large, network/model/credential-heavy reference evidence rather than bundled runtime scripts.
- `examples/smolagents_benchmark/` was treated as benchmark-scale reference evidence and skipped for runtime helpers.
- Generated caches, build outputs, and review/test artifacts are not runtime evidence.

Refresh this skill if public constructor signatures, CLI flags, optional extras, executor names, tool schema requirements, model provider wrappers, or documented workflows change in a newer checkout.
