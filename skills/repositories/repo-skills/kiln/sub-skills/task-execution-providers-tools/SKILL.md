---
name: task-execution-providers-tools
description: "Configure Kiln task execution through LiteLLM providers,
  structured outputs, prompts, built-in tools, skills, Kiln task tools, RAG tool
  references, and MCP tool sessions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kiln Task Execution, Providers, and Tools

Use this sub-skill when the task is about choosing a Kiln model/provider, building a task run configuration, invoking `adapter_for_task`, adding tool IDs to a run, diagnosing adapter errors, or explaining how Kiln maps prompts, structured outputs, thinking levels, skills, and MCP tools into model calls.

## Route first

- Use this sub-skill for `KilnAgentRunConfigProperties`, `McpRunConfigProperties`, `ToolsRunConfig`, `adapter_for_task`, provider/model registry questions, custom OpenAI-compatible models, structured output modes, thinking levels, prompt builder IDs, built-in tool IDs, `KilnToolInterface`, MCP tool IDs/sessions, skill tool routing, and Kiln task tools.
- Route persisted project/task/run/prompt/skill file creation, `.kiln` save/load, packaging, and schema persistence to the project-datamodel sub-skill.
- Route RAG indexing, document extraction, chunking, vector store setup, embeddings/rerankers, and content search readiness to the rag-documents-data sub-skill. This sub-skill only covers how a ready `RagTool` is exposed to task execution.
- Route REST endpoints, desktop provider forms, studio API behavior, MCP server startup/UI integration, OpenAPI, and web UI flows to the server-desktop-web-api sub-skill.
- Route fine-tune provider jobs, evals, prompt optimization, synthetic data, and repair workflows to the evals-optimization-finetuning sub-skill. This sub-skill only covers virtual provider mapping at run time.

## Load the right reference

- For run config construction and adapter invocation, read [references/run-configs-and-adapters.md](references/run-configs-and-adapters.md).
- For provider/model registries, custom providers, config keys, structured output modes, and thinking levels, read [references/model-provider-reference.md](references/model-provider-reference.md).
- For tool IDs, `KilnToolInterface`, built-in tools, skills, Kiln task tools, RAG tool routing, MCP IDs, and MCP session behavior, read [references/tools-skills-and-mcp.md](references/tools-skills-and-mcp.md).
- For common failures and recovery paths, read [references/troubleshooting.md](references/troubleshooting.md).

## Safe bundled script

Use `scripts/inspect_kiln_models.py` to inspect installed Kiln model/provider registries without calling external providers:

```bash
python scripts/inspect_kiln_models.py
python scripts/inspect_kiln_models.py --provider openai --limit 20
python scripts/inspect_kiln_models.py --provider openai --json
```

The script imports registries and prints counts/provider coverage only. It does not call model APIs, Ollama, Docker Model Runner, MCP servers, or paid services.

## Evidence notes

This sub-skill is distilled from repo-relative evidence in `libs/core/kiln_ai/datamodel/run_config.py`, `libs/core/kiln_ai/datamodel/tool_id.py`, `libs/core/kiln_ai/adapters/adapter_registry.py`, `libs/core/kiln_ai/adapters/provider_tools.py`, `libs/core/kiln_ai/adapters/ml_model_list.py`, `libs/core/kiln_ai/adapters/ml_embedding_model_list.py`, `libs/core/kiln_ai/adapters/reranker_list.py`, `libs/core/kiln_ai/adapters/prompt_builders.py`, `libs/core/kiln_ai/adapters/model_adapters/`, `libs/core/kiln_ai/tools/`, and `libs/core/kiln_ai/utils/config.py`, plus adapter/tool tests. Verified package evidence covered `kiln-ai`, `kiln-server`, and `kiln-studio-desktop` 1.0.4.
