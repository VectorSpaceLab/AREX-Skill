# Provider and Tool Integrations

## Optional Extras Matrix

mcp-agent keeps several provider and ecosystem packages optional. Install only the extras needed for the task:

| Capability | Extra or package family | Typical import surface |
| --- | --- | --- |
| OpenAI and OpenAI-compatible providers | `mcp-agent[openai]` | `mcp_agent.workflows.llm.augmented_llm_openai` |
| Anthropic API | `mcp-agent[anthropic]` | `mcp_agent.workflows.llm.augmented_llm_anthropic` |
| Anthropic on Bedrock | `mcp-agent[anthropic_bedrock]` plus AWS config | Anthropic wrapper with `anthropic.provider: bedrock` |
| Anthropic on Vertex AI | `mcp-agent[anthropic_vertex]` plus Google config | Anthropic wrapper with `anthropic.provider: vertexai` |
| Bedrock wrapper | `mcp-agent[bedrock]` | `mcp_agent.workflows.llm.augmented_llm_bedrock` |
| Azure wrapper | `mcp-agent[azure]` | `mcp_agent.workflows.llm.augmented_llm_azure` |
| Google wrapper | `mcp-agent[google]` | `mcp_agent.workflows.llm.augmented_llm_google` |
| Cohere wrapper | `mcp-agent[cohere]` | Cohere provider settings and wrapper imports |
| LangChain tools | `mcp-agent[langchain]` | `mcp_agent.tools.langchain_tool.from_langchain_tool` |
| CrewAI tools | `mcp-agent[crewai]` | `mcp_agent.tools.crewai_tool.from_crewai_tool` |
| Temporal tracing | `mcp-agent[temporal]` | Temporal executor and OpenTelemetry integration |
| Redis token/OAuth backing | `mcp-agent[redis]` | Redis-backed settings where configured |

The base package includes OpenTelemetry instrumentation dependencies, but provider SDKs such as `openai` and `anthropic` are still optional. Importing a provider wrapper without its SDK can raise `ModuleNotFoundError`; this is different from an authentication error caused by a missing or invalid API key.

## Distinguish Import, Key, and Model Errors

Use this order when diagnosing provider setup:

1. Import the wrapper module in a tiny Python check. `ModuleNotFoundError: No module named 'openai'`, `anthropic`, `crewai`, or `langchain_core` means install the matching extra.
2. Load or validate settings without printing secret values. Missing `api_key` fields indicate credential configuration, not package installation.
3. Check provider endpoint fields such as `base_url`, `endpoint`, `api_version`, deployment name, and `default_model`.
4. Only then run a live generation call if network and credentials are intentionally available.

`check_observability_config.py` follows the first three steps without importing provider SDKs or contacting external services.

## Provider Configuration Notes

Common settings fields:

```yaml
openai:
  default_model: "gpt-4o"
  reasoning_effort: "medium"      # none, low, medium, high
  base_url: null                   # set for OpenAI-compatible local/proxy endpoints

anthropic:
  provider: "anthropic"           # anthropic, bedrock, or vertexai
  default_model: "claude-sonnet-4-20250514"
  base_url: null

azure:
  endpoint: "https://example.openai.azure.com"
  api_version: "2025-04-01-preview"
  azure_deployment: "deployment-name"
  default_model: "gpt-4o-mini"

google:
  vertexai: false
  default_model: "gemini-2.0-flash"

lm_studio:
  base_url: "http://localhost:1234/v1"
  default_model: "openai/gpt-oss-20b"
```

Keep API keys in environment variables or secrets files. In generated diagnostics, redact keys, bearer tokens, authorization headers, and endpoint query secrets.

## Model Selection and Request Parameters

AugmentedLLM wrappers use provider defaults plus `RequestParams` overrides:

- OpenAI defaults to `gpt-4o` when no configured default is present and respects `openai.reasoning_effort` for reasoning models whose names start with `o1`, `o3`, `o4`, or `gpt-5`.
- Anthropic defaults depend on `anthropic.provider`: direct Anthropic, Bedrock, and Vertex AI use different model id formats.
- LM Studio prioritizes `RequestParams.model`, then `lm_studio.default_model`, then the OpenAI-compatible parent selector.
- `RequestParams.modelPreferences` can weight cost, speed, and intelligence when the wrapper selects a model from benchmarks.
- Unknown local model names may still work at the endpoint while producing incomplete cost metadata in token summaries.

## LM Studio and Local OpenAI-Compatible Endpoints

LM Studio uses the OpenAI-compatible client through `LMStudioAugmentedLLM`, but reads settings from `lm_studio` instead of `openai`. Defaults:

- `lm_studio.base_url`: `http://localhost:1234/v1`
- `lm_studio.api_key`: `lm-studio` for client compatibility
- `lm_studio.default_model`: must match the model loaded by the local server

Minimal pattern:

```python
from mcp_agent.workflows.llm.augmented_llm_lm_studio import LMStudioAugmentedLLM

llm = await agent.attach_llm(LMStudioAugmentedLLM)
result = await llm.generate_str("Use the available tools to inspect this directory")
```

Troubleshoot local providers by checking `/v1/models`, matching `default_model` to an actually loaded model, and confirming tool-calling or structured-output support for the selected model. Some small local models cannot reliably follow structured JSON schemas; LM Studio structured output uses a two-step text-then-JSON approach.

For Ollama or other OpenAI-compatible servers, use the OpenAI wrapper with `openai.base_url`, a compatibility API key value if needed, and a model id recognized by that server.

## LangChain Tool Adapter

`from_langchain_tool(lc_tool, name=None, description=None)` converts a LangChain tool into a plain Python callable suitable for mcp-agent function tools.

Supported shapes:

- `StructuredTool`: returns the underlying `.func` and preserves signature metadata.
- `BaseTool` with `_run`: wraps `_run` and copies its signature.
- Object with `run`: wraps `run` and copies signature when inspectable.
- Plain callable: wraps the callable and copies signature when inspectable.

Failure mode: invalid objects raise `ValueError` explaining that a LangChain tool must expose `func`, `_run`, `run`, or be callable. If `langchain_core` is missing, importing the adapter raises `ModuleNotFoundError` before conversion starts.

Example:

```python
from mcp_agent.tools.langchain_tool import from_langchain_tool

search_fn = from_langchain_tool(search_tool, name="web_search")
agent = Agent(name="search_agent", functions=[search_fn])
```

## CrewAI Tool Adapter

`from_crewai_tool(crewai_tool, name=None, description=None)` converts CrewAI tools into mcp-agent function tools.

Supported shapes:

- Decorated CrewAI tool with `.func`: returns the underlying function and sets name/docstring.
- Class-based CrewAI tool with `args_schema` and `_run`: builds a wrapper whose signature is derived from Pydantic model fields, with required fields before optional fields.
- Object with `run`: wraps `run` with generic arguments.
- Plain callable: wraps and copies signature when inspectable.

CrewAI tool names containing spaces are normalized to lowercase underscores unless an explicit name override is supplied. Invalid objects raise `ValueError`. If `crewai` is missing, importing the adapter raises `ModuleNotFoundError`.

Example:

```python
from mcp_agent.tools.crewai_tool import from_crewai_tool

agent = Agent(
    name="research_agent",
    functions=[from_crewai_tool(search_tool), from_crewai_tool(file_tool)],
)
```

## Integration Safety Defaults

- Do not import every provider wrapper just to inspect config; imports can fail when extras are intentionally absent.
- Do not log raw prompts, responses, API keys, authorization headers, or local filesystem secrets unless the user explicitly requests a controlled debug dump.
- Install the smallest extra set that matches the task; avoid broad dependency groups when only tracing or adapter inspection is needed.
- For cloud log CLI commands, deployment state, or hosted environment configuration, route to `../cli-cloud-operations/SKILL.md`.
