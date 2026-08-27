# Run Configs and Adapters

This reference covers how Kiln turns a saved or ad-hoc task run configuration into an executable adapter. It is intentionally limited to execution configuration; persisted project/task/run files belong to the project-datamodel sub-skill.

## Core execution choice

`adapter_for_task(kiln_task, run_config_properties, base_adapter_config=None)` is the main routing helper.

- `run_config_properties.type == "kiln_agent"` returns a `LiteLlmAdapter`.
- `run_config_properties.type == "mcp"` returns an `MCPAdapter`.
- Unknown or mismatched property classes raise `ValueError` early.

Typical high-level flow:

1. Load or construct a `Task` and a `TaskRunConfig` elsewhere.
2. Use the `TaskRunConfig.run_config_properties` value here.
3. If the run uses skill tool IDs, call `load_skills_for_task(task, run_config_properties)` once and pass the returned dict into `AdapterConfig(skills=...)`.
4. Build the adapter with `adapter_for_task`.
5. Call `await adapter.invoke(input)` or `await adapter.invoke_returning_run_output(input)`.

Invoking a LiteLLM adapter calls the selected model provider and therefore requires credentials or a reachable local service unless the provider is mocked by a test. Do not use invocation as a registry smoke check; use the bundled model inspection script instead.

## `KilnAgentRunConfigProperties`

Use `KilnAgentRunConfigProperties` for normal AI-agent task execution through LiteLLM-backed providers.

Important fields:

| Field | Meaning | Notes |
|---|---|---|
| `type` | Literal `"kiln_agent"` | Default when run config type is omitted. |
| `model_name` | Kiln model enum string, provider model slug, fine-tune id, `user_model::<id>`, or legacy custom slug | Must match the selected provider path. |
| `model_provider_name` | `ModelProviderName` enum value | Determines auth/config lookup and LiteLLM provider mapping. |
| `prompt_id` | Built-in prompt generator or frozen prompt id | See prompt builder section below. |
| `top_p` | Sampling nucleus, default `1.0` | Valid range is `0 <= top_p <= 1`. |
| `temperature` | Sampling temperature, default `1.0` | Valid range is `0 <= temperature <= 2`. Some models reject custom `top_p` and `temperature` together. |
| `structured_output_mode` | `StructuredOutputMode` | Determines API response format/tool-call JSON behavior. |
| `thinking_level` | Optional non-empty string | Used only when the resolved provider entry has thinking levels. |
| `tools_config` | Optional `ToolsRunConfig` | Tool IDs available to the model. |
| `input_transform` | Optional input transform | Rendered before prompt formatting. Deep validation belongs to project-datamodel. |

Concrete object example:

```python
from kiln_ai.adapters.adapter_registry import adapter_for_task, load_skills_for_task
from kiln_ai.adapters.model_adapters.base_adapter import AdapterConfig
from kiln_ai.datamodel import Task
from kiln_ai.datamodel.datamodel_enums import ModelProviderName, StructuredOutputMode
from kiln_ai.datamodel.prompt_id import PromptGenerators
from kiln_ai.datamodel.run_config import KilnAgentRunConfigProperties, ToolsRunConfig
from kiln_ai.datamodel.tool_id import KilnBuiltInToolId, build_skill_tool_id

# A transient task is enough for ad-hoc execution. Use project-datamodel when
# creating or saving a .kiln project/task/run config.
task = Task(
    name="classify-ticket",
    instruction="Return a support ticket category.",
    output_json_schema='{"type":"object","properties":{"category":{"type":"string"}},"required":["category"]}',
)

run_config = KilnAgentRunConfigProperties(
    model_name="gpt_5_5",
    model_provider_name=ModelProviderName.openai,
    prompt_id=PromptGenerators.SIMPLE,
    structured_output_mode=StructuredOutputMode.json_schema,
    temperature=0.2,
    top_p=1.0,
    tools_config=ToolsRunConfig(
        tools=[
            KilnBuiltInToolId.ADD_NUMBERS.value,
            build_skill_tool_id("ticket-triage-guidance"),
        ]
    ),
)

skills = load_skills_for_task(task, run_config)
adapter = adapter_for_task(
    task,
    run_config,
    base_adapter_config=AdapterConfig(allow_saving=False, skills=skills),
)
# await adapter.invoke("The customer cannot reset their password.")
```

Notes:

- `allow_saving=False` prevents autosaved `TaskRun` files for ad-hoc SDK calls.
- Skill tool IDs require preloaded skills through `AdapterConfig(skills=...)`; otherwise the adapter raises a direct error.
- Tool names must be unique after resolving registry tools, skill tool, and unmanaged tools.
- The code above would call OpenAI if invoked. Replace the provider/model and credentials or mock the adapter in tests.

## `McpRunConfigProperties`

Use `McpRunConfigProperties` when a Kiln task is executed directly by one MCP tool instead of by a model agent.

Key shape:

```python
from kiln_ai.datamodel.run_config import MCPToolReference, McpRunConfigProperties

run_config = McpRunConfigProperties(
    tool_reference=MCPToolReference(
        tool_id="mcp::remote::customer_crm::lookup_customer",
        tool_server_id="customer_crm",
        tool_name="lookup_customer",
        input_schema={
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
        output_schema={
            "type": "object",
            "properties": {"tier": {"type": "string"}},
            "required": ["tier"],
        },
    )
)
```

The project must contain the corresponding external tool server; resolving/saving that server belongs to project-datamodel. Server startup, API routes, and UI forms belong to server-desktop-web-api.

MCP adapter behavior:

- It is single-turn. `prior_trace` and `parent_task_run` continuation are not supported.
- If the task has no input schema, string input is mapped to the MCP tool's single string field when the tool input schema has exactly one such field; otherwise it uses `input`.
- If the task has structured input, dict input is passed through as tool arguments.
- Structured task output is parsed from tool output and validated against the task output schema.
- Runtime failures are wrapped as `KilnRunError` with no partial trace because MCP direct runs do not create a multi-message LLM trace.

## `ToolsRunConfig`

`ToolsRunConfig(tools=[...])` is just the list of `ToolId` strings made available to a `kiln_agent` run. The list can contain:

- Built-in Kiln tool IDs such as `kiln_tool::add_numbers`.
- RAG tool IDs such as `kiln_tool::rag::<rag_config_id>` when the RAG config and vector store are already ready.
- MCP tool IDs such as `mcp::remote::<server_id>::<tool_name>` or `mcp::local::<server_id>::<tool_name>`.
- Kiln task tool IDs such as `kiln_task::<server_id>`.
- Skill tool IDs such as `kiln_tool::skill::<skill_id>`.
- SDK-injected unmanaged tool IDs such as `kiln_unmanaged::<slug>` when supplied through `AdapterConfig.unmanaged_tools`.

Do not put fine-tune job IDs, provider names, or arbitrary strings into `ToolsRunConfig`; the `ToolId` validator will reject unknown formats.

## `AdapterConfig`

`AdapterConfig` controls execution metadata and SDK integration without changing the persisted model-facing run config.

Important fields:

| Field | Use |
|---|---|
| `allow_saving` | Controls whether adapter-created runs and nested Kiln task tool calls may save outputs when autosave is enabled. |
| `top_logprobs` | Requests logprobs on final calls; if no logprobs return, the adapter raises. |
| `default_tags` | Tags added to generated `TaskRun` objects, e.g. `tool_call` for nested task tools. |
| `task_run_config_id` | Records which saved run config originated the run. |
| `prompt_builder` | Overrides prompt construction with a custom builder. |
| `skills` | Preloaded skill objects keyed by skill ID. Required when skill tool IDs are referenced. |
| `return_on_tool_call` | Returns control to caller when a normal tool call is requested instead of running the tool internally. |
| `unmanaged_tools` | Extra SDK-provided `KilnToolInterface` objects; names must not collide. |
| `automatic_prompt_caching` | Adds provider-specific prompt caching hints where supported. |

## Prompt builders

`prompt_id` can be a built-in prompt generator or a frozen prompt reference.

Built-in generators:

- `simple_prompt_builder`
- `few_shot_prompt_builder`
- `multi_shot_prompt_builder`
- `repairs_prompt_builder`
- `simple_chain_of_thought_prompt_builder`
- `few_shot_chain_of_thought_prompt_builder`
- `multi_shot_chain_of_thought_prompt_builder`

Frozen prompt reference formats:

- `id::<prompt_id>` loads a saved prompt on the task.
- `task_run_config::<project_id>::<task_id>::<task_run_config_id>` loads a prompt snapshot from a task run config.
- `fine_tune_prompt::<project_id>::<task_id>::<fine_tune_id>` loads the system prompt associated with a fine-tune; detailed fine-tune workflows route to evals-optimization-finetuning.

Prompt builder behavior:

- Simple prompts use task instruction and requirements.
- Few-shot and multi-shot prompts collect high-quality or repaired task runs as examples.
- Repairs prompts include initial bad output, repair instructions, and repaired output when available.
- Chain-of-thought prompt builders add thinking instructions. The adapter chooses a chat strategy based on the prompt, model reasoning capability, and tuned chat strategy.
- When structured output mode is `json_instructions` or `json_instruction_and_object`, the prompt builder receives `include_json_instructions=True` so schema instructions are appended to the prompt.
- Available skills are appended to the system prompt via a Skills section when skill IDs resolve through `AdapterConfig(skills=...)`.

## Adapter output and trace behavior

On successful runs, adapters generate a `TaskRun` with:

- Original input preserved as string or JSON string.
- `TaskOutput.output` as string for unstructured tasks or JSON string for structured dict output.
- `TaskOutput.source.run_config` containing the run config snapshot.
- Adapter properties such as `adapter_name`, `model_name`, `model_provider`, `prompt_id`, `structured_output_mode`, `temperature`, and `top_p` for `kiln_agent` runs.
- Trace and cumulative usage when available.

For LiteLLM runs:

- Input schemas are validated before provider calls.
- Input transforms render before chat formatting.
- Structured output is parsed and validated after the provider or `task_response` tool returns.
- Runtime provider/tool failures are wrapped in `KilnRunError` with a partial trace when one can be recovered.
- A root invocation creates an agent run context used by MCP tool calls and cleans up MCP sessions when the root run completes.

For MCP direct runs:

- The trace is a synthetic single user/assistant pair built from tool input/output.
- Provider usage is `None` because no model provider is called.

## Evidence notes

Repo-relative source evidence: `libs/core/kiln_ai/datamodel/run_config.py`, `libs/core/kiln_ai/adapters/adapter_registry.py`, `libs/core/kiln_ai/adapters/model_adapters/base_adapter.py`, `libs/core/kiln_ai/adapters/model_adapters/litellm_adapter.py`, `libs/core/kiln_ai/adapters/model_adapters/mcp_adapter.py`, `libs/core/kiln_ai/adapters/prompt_builders.py`, and adapter tests.
