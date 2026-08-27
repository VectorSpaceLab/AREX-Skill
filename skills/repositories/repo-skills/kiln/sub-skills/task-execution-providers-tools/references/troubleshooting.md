# Troubleshooting Task Execution, Providers, and Tools

Use this reference when a Kiln task run, provider lookup, structured output, tool call, skill load, or MCP session fails. For persisted `.kiln` file validation use project-datamodel; for RAG indexing/vector stores use rag-documents-data; for REST/UI/provider forms use server-desktop-web-api; for fine-tune job flows use evals-optimization-finetuning.

## Fast triage checklist

1. Identify run config type:
   - `kiln_agent` means LiteLLM provider execution, optional tools, prompts, structured output, and thinking levels.
   - `mcp` means direct single MCP tool execution with no model call.
2. Inspect the run config fields without invoking providers.
3. Validate `model_provider_name`, `model_name`, `prompt_id`, `structured_output_mode`, `temperature`, `top_p`, and `tools_config.tools`.
4. If model/provider registry facts are needed, run:

   ```bash
   python scripts/inspect_kiln_models.py --provider <provider>
   ```

5. If tools are enabled, classify every tool ID by prefix and resolve only safe local definitions first.
6. If the failure involves credentials, local services, MCP servers, paid flows, Copilot, Ollama, or cloud providers, treat the dependency as optional unless the user's task explicitly requires that live service.

## Environment import gotchas

These are verified environment issues for Kiln 1.0.4 and current source behavior.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `kiln_ai.tools` import fails after installing current unconstrained MCP packages | `mcp` package version is not lock-compatible; current tools imports worked with `mcp[cli]==1.10.1` | Pin or install lock-compatible `mcp[cli]==1.10.1` in the environment used for Kiln tools/MCP inspection. |
| `kiln_server` import fails around `starlette._utils.collapse_excgroups` | Starlette version too new/incompatible; `1.6.0` was incompatible while `0.52.1` worked | Use a Starlette version compatible with Kiln's lock constraints, verified at `0.52.1` for this evidence set. |
| RAG vector-store import fails with missing `pandas` | LanceDB vector-store dependency path imports pandas through llama-index vector-store packages | Install `pandas` for LanceDB-backed RAG inspection/runs, then route RAG setup and indexing details to rag-documents-data. |
| Provider, Ollama, Copilot, cloud LanceDB, or fine-tune smoke fails due to missing service/credentials | Live external flow is optional by default | Do not treat as a core task-execution skill failure unless the user's task requires that service. Ask for credentials/service readiness before live calls. |

## Missing provider credentials

Common messages:

- `Attempted to use OpenAI without an API key set`
- `Attempted to use OpenRouter without an API key set`
- `Attempted to use Gemini without an API key set`
- `Authentication with the model provider failed. Check your API key.`

Recovery:

1. Confirm the selected provider enum value and required config keys in [model-provider-reference.md](model-provider-reference.md).
2. Set the relevant environment variable or user config value. Examples: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AZURE_OPENAI_API_KEY` plus `AZURE_OPENAI_ENDPOINT`, `VERTEX_PROJECT_ID`, or AWS keys for Bedrock.
3. Never commit real keys into project files, tests, run configs, generated skill files, or screenshots.
4. Re-run a minimal safe registry inspection first, then a real provider call only if the task requires it.
5. For local Ollama or Docker Model Runner, verify the service is running and the model is installed; registry inspection alone does not prove local model availability.

## Bad provider/model slug

Symptoms:

- Pydantic error such as `Input should be ...` for `model_provider_name`.
- `model_name and model_provider_name must be provided`.
- `model_provider_name <provider> not found for model <model>`.
- `Invalid custom model ID`.
- `Invalid openai compatible model ID`.
- `User model <id> not found`.
- `OpenAI compatible provider <name> not found`.
- `OpenAI compatible provider <name> has no base URL`.

Recovery:

1. Check `model_provider_name` is one of the provider enum values listed in [model-provider-reference.md](model-provider-reference.md).
2. For built-in models, inspect the installed registry:

   ```bash
   python scripts/inspect_kiln_models.py --provider openai --limit 50
   ```

3. For direct OpenAI-compatible providers, keep the full legacy slug in `model_name`:

   ```text
   provider_name::model_id
   ```

   Both parts must be non-empty. The adapter preserves the full slug for persistence and strips the provider prefix only at the LiteLLM boundary.
4. For `user_model::<entry_id>`, verify a matching `user_model_registry` entry exists. For custom entries, ensure `provider_id` names an `openai_compatible_providers` record; for builtin entries, ensure `provider_id` is a valid provider enum value.
5. For legacy `kiln_custom_registry`, preserve `provider::model_id`; changing the slug breaks historical run matching.
6. For fine-tuned model IDs, route job status/model availability to evals-optimization-finetuning. At run time, unfinished fine-tunes raise when no provider model ID is available.

## OpenAI-compatible base URL issues

Symptoms:

- `Explicit Base URL is required for OpenAI compatible APIs`
- connection refused to a local endpoint
- provider returns 404/unsupported path
- model slug looks right but LiteLLM cannot route it

Recovery:

1. For `openai_compatible`, configure `openai_compatible_providers` with the exact `name` referenced before `::` in `model_name`.
2. Include the API path expected by that server, commonly `/v1`.
3. Keep `api_key` optional only for services that truly do not require it; the adapter substitutes a dummy key for some local providers but custom providers use the configured record.
4. For Ollama and Docker Model Runner, prefer their dedicated provider enum values unless the user intentionally created a custom provider record.
5. Test the local service separately before blaming Kiln's model registry.

## Structured output mismatch

Symptoms:

- `The model's output didn't match the expected format.`
- `structured response is not a dict`
- schema validation errors after a provider accepted the request
- `Function calling/tools can't be used as the JSON response format if you're also using tools`
- model returns fenced JSON/prose under `json_instructions`

Recovery:

1. Confirm the task actually has `output_json_schema`; unstructured tasks require string output.
2. Pick a structured output mode compatible with both provider and tools:
   - Use `json_schema` when the provider supports schema response format.
   - Use `json_mode` or `json_instruction_and_object` when the provider supports JSON object mode but not schema enforcement.
   - Use `json_instructions` for untested/custom providers.
   - Avoid `function_calling` and `function_calling_weak` when normal runtime tools are enabled.
3. If provider rejects schema details, simplify the schema. Kiln closes object schemas and strips numeric bounds before sending JSON schema, but provider-specific limitations may remain.
4. If output validates as JSON but not against schema, improve prompt requirements or choose a stronger structured output mode/model.
5. If the model uses custom/fine-tuned formatting, verify any parser/formatter flags in the model provider entry.
6. For saved prompt IDs or fine-tune prompts, ensure the frozen prompt actually contains JSON instructions when using `json_custom_instructions`.

## Thinking-level and reasoning errors

Symptoms:

- `thinking_level must be a non-empty string when provided`.
- provider rejects a reasoning parameter
- `Reasoning is required for this model, but no reasoning was returned.`
- `top_p and temperature can not both have custom values for this model`

Recovery:

1. Use `scripts/inspect_kiln_models.py --provider <provider> --limit ...` to identify models with thinking levels.
2. Only set `thinking_level` to values supported by the resolved provider entry. Labels such as `Low` and wire values such as `low` are not interchangeable unless the registry says so.
3. If provider rejects reasoning for `none`, remove `thinking_level` or use the provider default. Anthropic native `none` is intentionally omitted by the adapter, but stale configs can still fail elsewhere.
4. If reasoning is required but absent, choose a model/provider entry with reliable reasoning output, disable structured output only if acceptable, or select a non-reasoning model.
5. For `temp_top_p_exclusive` models, customize only one of `temperature` or `top_p`; leave the other at `1.0`.

## Tool ID validation failures

Symptoms:

- `Invalid tool ID`
- `Invalid remote MCP tool ID`
- `Invalid local MCP tool ID`
- `Invalid RAG tool ID`
- `Invalid Kiln task tool ID`
- `Invalid skill tool ID`
- `Tool ID <id> not found in tool registry`

Recovery:

1. Match the ID exactly to one of the formats in [tools-skills-and-mcp.md](tools-skills-and-mcp.md).
2. Built-in tool IDs must use the exact `kiln_tool::...` strings; do not use function names such as `add` in `ToolsRunConfig`.
3. MCP tool IDs must have exactly four `::`-separated parts: `mcp::<remote|local>::<server_id>::<tool_name>`.
4. RAG, skill, and Kiln task IDs must include a non-empty config/server/skill ID.
5. Unmanaged tool IDs must be `kiln_unmanaged::<slug>` and require a matching object in `AdapterConfig.unmanaged_tools`.

## Tool resolution and duplicate names

Symptoms:

- `Unable to resolve tool from id ... Requires a parent project/task.`
- `External tool server not found`
- `RAG config not found`
- `Skill tool IDs are resolved by the adapter, not tool_from_id`
- `Each tool must have a unique name`
- `Duplicate tool name ... unmanaged and registry tools must have unique names`

Recovery:

1. Ensure the task has a parent project before resolving project-scoped MCP, Kiln task, or RAG tools.
2. Verify the project contains the external tool server or RAG config named in the tool ID. Persisted project inspection belongs to project-datamodel.
3. Do not call `tool_from_id` for skill IDs. Use `load_skills_for_task` and pass `AdapterConfig(skills=...)`.
4. Rename duplicate tools or de-select one. Model tool behavior is undefined when function names collide.
5. For unmanaged SDK tools, ensure each tool object implements `KilnToolInterface` and has a unique function name.

## Skill tool load failures

Symptoms:

- `Run config references skills but no skills dict was provided via AdapterConfig(skills=...)`
- `Skill <id> referenced in run config but not found in the injected skills dict`
- `Duplicate skill name`
- skill resource errors such as invalid prefix or missing file

Recovery:

1. Call `load_skills_for_task(task, run_config)` before constructing the adapter.
2. Pass the resulting dict into `AdapterConfig(skills=skills)`.
3. Ensure every `kiln_tool::skill::<skill_id>` exists under the parent project and is not archived/inaccessible.
4. Keep skill names unique; the runtime tool is called by skill name, not skill ID.
5. Resource paths must be listed by the skill and start with `references/` or `assets/`. Never guess paths.

## MCP session and tool failures

Symptoms:

- `MCP tool call attempted without an agent run context`
- `server_url is required`
- `Attempted to start local MCP server, but no command was provided`
- `args is not a list of strings`
- `Tool <name> not found`
- `Tool returned invalid structured content`
- `Tool returned no content`
- `First block must be a text block`
- `Tool returned multiple content blocks, expected one`
- `Session continuation is not supported for MCP adapter`

Recovery:

1. Decide whether this is MCP as an agent tool or direct `McpRunConfigProperties`. Direct MCP runs are single-turn and cannot continue prior traces.
2. For remote MCP, validate `server_url`, headers, and secret header keys. Secret values should be in `mcp_secrets`, keyed as `server_id::key_name`.
3. For local MCP, validate command, args list, env var names, and secret env var keys.
4. If local commands such as `npx` are not found, set `CUSTOM_MCP_PATH` or `custom_mcp_path` so Kiln uses that PATH instead of shell detection.
5. If the server starts but tool lookup fails, list server tools through the appropriate server/API flow and update the tool name in the ID.
6. If content shape is incompatible, fix the MCP server tool to return one text block or dict `structuredContent` as expected by `MCPServerTool`.
7. If the error appears only with current package resolution, ensure the environment uses lock-compatible `mcp[cli]==1.10.1`.

## Kiln task tool failures

Symptoms:

- `Project not found`
- `Task not found`
- `Task run config not found`
- `Input not found in kwargs`
- nested adapter/provider errors inside a tool call

Recovery:

1. Verify the external tool server's `task_id`, `run_config_id`, name, and description in the parent project.
2. For plaintext target tasks, pass an `input` string argument.
3. For structured target tasks, pass kwargs matching the target task input schema.
4. Remember nested task tool calls use the target task's saved run config, not the caller's model/provider.
5. If the nested run uses skills, the tool preloads them through `load_skills_for_task`; missing project skills still fail.
6. Set `allow_saving` intentionally in the outer `AdapterConfig`; it controls nested task tool saving behavior through `ToolCallContext`.

## RAG tool failures at execution boundary

Symptoms:

- `RAG config not found`
- `Vector store config not found`
- `Embedding config not found`
- `No embeddings generated`
- empty or low-quality search results

Recovery:

1. Confirm only the tool ID format and project parentage here.
2. Route vector store, embeddings, document ingestion, chunk availability, LanceDB, rerankers, and search quality to rag-documents-data.
3. If import fails before execution because `pandas` is missing, install `pandas` in the Kiln environment used for LanceDB-backed RAG work.

## Provider/network runtime errors

Kiln formats common LiteLLM errors for users:

| Underlying class | User-facing message | Recovery |
|---|---|---|
| Rate limit | `Rate limit exceeded. Wait a moment and try again.` | Back off, reduce concurrency, or use another provider/model. |
| Authentication | `Authentication with the model provider failed. Check your API key.` | Verify provider key/endpoint/project. |
| API connection | `Could not connect to the model provider. Check your network connection.` | Check network, local service, proxy, or base URL. |
| Service unavailable/5xx | `The model provider is currently unavailable. Try again in a moment.` | Retry later or switch provider. |
| JSON schema validation | `The model's output didn't match the expected format.` | See structured output section. |

Unknown exceptions are intentionally collapsed to a generic message to avoid leaking provider internals; inspect logs or the original exception in a controlled development environment when necessary.

## Paid and optional service boundary

The following flows are optional unless explicitly requested and provisioned by the user:

- paid/prerelease hosted provider calls
- Ollama/local model downloads and service startup
- Docker Model Runner service startup
- Copilot calls
- cloud LanceDB/provider-hosted RAG services
- fine-tune provider job submission/status/deployment
- live MCP servers outside local safe mocks

Do not create credentials, consume paid quota, download large models, or start long-running services as a routine troubleshooting step.

## Evidence notes

Repo-relative source evidence: `libs/core/kiln_ai/adapters/errors.py`, `libs/core/kiln_ai/adapters/model_adapters/base_adapter.py`, `libs/core/kiln_ai/adapters/model_adapters/litellm_adapter.py`, `libs/core/kiln_ai/adapters/model_adapters/mcp_adapter.py`, `libs/core/kiln_ai/adapters/provider_tools.py`, `libs/core/kiln_ai/datamodel/run_config.py`, `libs/core/kiln_ai/datamodel/tool_id.py`, `libs/core/kiln_ai/tools/`, `libs/core/kiln_ai/utils/config.py`, and adapter/tool tests.
