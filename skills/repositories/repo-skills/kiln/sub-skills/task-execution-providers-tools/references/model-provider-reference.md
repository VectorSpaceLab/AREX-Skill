# Model and Provider Reference

This reference covers Kiln's provider/model registries, custom OpenAI-compatible providers, config keys, structured output modes, and thinking levels. It is safe to inspect registries locally; do not call live providers just to discover model metadata.

Use `scripts/inspect_kiln_models.py` from this sub-skill to print installed registry counts and provider coverage without making provider, Ollama, Docker Model Runner, MCP, or network calls.

## Registry shape

Kiln keeps separate registries for:

- Chat/task execution models: `built_in_models` in `ml_model_list.py`.
- Embedding models: `built_in_embedding_models` in `ml_embedding_model_list.py`.
- Reranker models: `built_in_rerankers` in `reranker_list.py`.
- User-defined chat models: `user_model_registry` and legacy `custom_models` in `Config`.
- Custom OpenAI-compatible provider endpoints: `openai_compatible_providers` in `Config`.

Verified 1.0.4 evidence showed 242 built-in chat models, 33 built-in embedding models, 4 rerankers, and 19 provider enum values. Treat these as version evidence, not a promise for later releases.

Provider enum values in 1.0.4:

```text
openai
groq
amazon_bedrock
ollama
openrouter
fireworks_ai
kiln_fine_tune
kiln_custom_registry
openai_compatible
anthropic
gemini_api
azure_openai
huggingface
vertex
together_ai
siliconflow_cn
cerebras
docker_model_runner
featherless_ai
```

`KilnModelProvider` entries contain more than provider/model IDs. Fields commonly used by adapters include:

- `model_id`: provider-specific ID sent to LiteLLM.
- `supports_structured_output`, `structured_output_mode`, `supports_function_calling`.
- `supports_data_gen`, `suggested_for_data_gen`, `suggested_for_evals`.
- `reasoning_capable`, `available_thinking_levels`, `default_thinking_level`.
- Provider-specific toggles such as OpenRouter reasoning object support, Anthropic extended/summarized thinking, Gemini reasoning, SiliconFlow thinking, and `temp_top_p_exclusive`.
- `parser` and `formatter` for models that need custom output parsing or request formatting.
- Multimodal/document extraction support flags. Detailed document/RAG extraction routes to rag-documents-data.

## Safe registry inspection

Examples:

```bash
python scripts/inspect_kiln_models.py
python scripts/inspect_kiln_models.py --provider openrouter --limit 10
python scripts/inspect_kiln_models.py --provider openai --json
```

The script reads registry objects directly. It intentionally avoids these calls because they can touch external services or credentials:

- `provider_enabled(...)`
- Ollama or Docker Model Runner connection probes
- actual `adapter.invoke(...)`
- MCP sessions
- any LiteLLM completion call

## Provider config keys and environment variables

Kiln's `Config` object can read settings from a user settings store, in-memory settings, and selected environment variables. Sensitive values should never be committed to projects, examples, or generated skill files.

### Provider auth and service keys

| Config key | Environment variable | Provider/use |
|---|---|---|
| `open_ai_api_key` | `OPENAI_API_KEY` | OpenAI |
| `groq_api_key` | `GROQ_API_KEY` | Groq |
| `open_router_api_key` | `OPENROUTER_API_KEY` | OpenRouter |
| `fireworks_api_key` | `FIREWORKS_API_KEY` | Fireworks AI |
| `fireworks_account_id` | `FIREWORKS_ACCOUNT_ID` | Fireworks account-specific operations |
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | Anthropic |
| `gemini_api_key` | `GEMINI_API_KEY` | Gemini API |
| `azure_openai_api_key` | `AZURE_OPENAI_API_KEY` | Azure OpenAI |
| `azure_openai_endpoint` | `AZURE_OPENAI_ENDPOINT` | Azure OpenAI base endpoint |
| `huggingface_api_key` | `HUGGINGFACE_API_KEY` | Hugging Face |
| `vertex_project_id` | `VERTEX_PROJECT_ID` | Vertex/Gemini Enterprise Agent Platform |
| `vertex_location` | `VERTEX_LOCATION` | Vertex region/location |
| `together_api_key` | `TOGETHERAI_API_KEY` | Together AI |
| `siliconflow_cn_api_key` | `SILICONFLOW_CN_API_KEY` | SiliconFlow |
| `cerebras_api_key` | `CEREBRAS_API_KEY` | Cerebras |
| `featherless_ai_api_key` | `FEATHERLESS_AI_API_KEY` | Featherless AI |
| `bedrock_access_key` | `AWS_ACCESS_KEY_ID` | Amazon Bedrock |
| `bedrock_secret_key` | `AWS_SECRET_ACCESS_KEY` | Amazon Bedrock |
| `kiln_copilot_api_key` | `KILN_COPILOT_API_KEY` | Copilot flows; route endpoint/UI details to server-desktop-web-api |
| `wandb_api_key` | `WANDB_API_KEY` | Weights & Biases fine-tune/eval integrations; route job flows to evals-optimization-finetuning |
| `wandb_entity` | `WANDB_ENTITY` | Weights & Biases entity |
| `wandb_base_url` | `WANDB_BASE_URL` | Weights & Biases base URL |

### Local services and execution behavior

| Config key | Environment variable | Use |
|---|---|---|
| `ollama_base_url` | `OLLAMA_BASE_URL` | Ollama OpenAI-compatible base. Defaults to local Ollama if unset. |
| `docker_model_runner_base_url` | `DOCKER_MODEL_RUNNER_BASE_URL` | Docker Model Runner OpenAI-compatible base. |
| `custom_mcp_path` | `CUSTOM_MCP_PATH` | PATH override used when launching local MCP commands such as `npx`. |
| `kiln_local_api_host` | `KILN_LOCAL_API_HOST` | In-memory local server host for `call_kiln_api`. |
| `kiln_local_api_port` | `KILN_LOCAL_API_PORT` | In-memory local server port for `call_kiln_api`. |
| `autosave_runs` | `KILN_AUTOSAVE_RUNS` | Controls default run autosaving. |
| `user_id` | `KILN_USER_ID` | Used as default human-created data source metadata. |
| `enable_demo_tools` | `ENABLE_DEMO_TOOLS` | Enables demo tool surfaces where used. |

### Settings-only keys

These are stored through `Config` rather than direct provider env variables:

- `projects`: known projects list.
- `custom_models`: legacy custom model slugs in `provider::model_id` format.
- `user_model_registry`: new custom/user model entries.
- `openai_compatible_providers`: custom provider endpoint records with `name`, `base_url`, and optional `api_key`.
- `mcp_secrets`: secret headers/env vars for MCP servers, keyed by `mcp_server_id::key_name`.
- `git_sync_projects`: Git sync settings; route Git sync details to server-desktop-web-api or repo-development.
- `user_type`, `work_use_contact`, `personal_use_contact`: product settings; do not infer or decide user/legal status.

## Provider warning gates

`provider_warnings` defines required config keys for common hosted providers. Missing keys cause provider lookup or adapter setup to raise errors before a useful model call can happen.

Providers with warning gates in 1.0.4:

```text
amazon_bedrock
anthropic
azure_openai
cerebras
featherless_ai
fireworks_ai
gemini_api
groq
huggingface
openai
openrouter
siliconflow_cn
together_ai
vertex
```

Ollama and Docker Model Runner are checked by local connection probes when `provider_enabled(...)` is called, but ordinary registry inspection should not call that function.

## LiteLLM provider mapping

`lite_llm_core_config_for_provider(provider_name, openai_compatible_provider_name=None)` maps Kiln provider names to LiteLLM kwargs and auth details.

Important mappings:

| Kiln provider | LiteLLM/provider behavior |
|---|---|
| `openai`, `groq`, `anthropic`, `gemini_api`, `fireworks_ai`, `huggingface`, `together_ai`, `cerebras`, `featherless_ai` | Native LiteLLM provider mapping with API key in `additional_body_options`. |
| `openrouter` | Base URL default `https://openrouter.ai/api/v1`, Kiln headers, OpenRouter key. |
| `siliconflow_cn` | OpenAI-compatible base URL default `https://api.siliconflow.cn/v1`, Kiln headers, SiliconFlow key. |
| `amazon_bedrock` | AWS access key, secret key, and default region `us-west-2`. |
| `azure_openai` | Azure endpoint, key, and API version. |
| `vertex` | Vertex project and location. |
| `ollama` | Uses Ollama's OpenAI-compatible `/v1` endpoint and dummy API key `NA`. |
| `docker_model_runner` | Uses Docker Model Runner OpenAI-compatible `/v1` endpoint and dummy API key `DMR`. |
| `openai_compatible` | Requires a configured provider name to look up `base_url` and optional `api_key`. |
| `kiln_fine_tune`, `kiln_custom_registry` | Virtual providers that must map to an underlying provider before LiteLLM config lookup. Fine-tune job details route to evals-optimization-finetuning. |

`get_litellm_provider_info(...)` then converts the resolved `KilnModelProvider` to a LiteLLM model string such as `openai/<model_id>`, `openrouter/<model_id>`, or an OpenAI-compatible custom string. Custom providers, Ollama, Docker Model Runner, fine-tunes, and legacy custom registry models require an explicit base URL path upstream.

## Custom OpenAI-compatible providers

There are two active custom-model paths plus one legacy path.

### 1. Direct legacy OpenAI-compatible run config

Use provider `openai_compatible` and a model slug of the form `provider_name::model_id`.

```python
from kiln_ai.datamodel.datamodel_enums import ModelProviderName, StructuredOutputMode
from kiln_ai.datamodel.prompt_id import PromptGenerators
from kiln_ai.datamodel.run_config import KilnAgentRunConfigProperties

run_config = KilnAgentRunConfigProperties(
    model_name="local-vllm::meta-llama/Llama-3.1-8B-Instruct",
    model_provider_name=ModelProviderName.openai_compatible,
    prompt_id=PromptGenerators.SIMPLE,
    structured_output_mode=StructuredOutputMode.json_instructions,
)
```

The provider name before `::` must match a configured `openai_compatible_providers` entry. The full slug stays on `run_config.model_name` for persistence and rehydration; the adapter strips only the provider prefix when building the LiteLLM model provider.

Recovery hints:

- `Invalid openai compatible model ID`: ensure the slug has exactly a non-empty provider and model part separated by `::`.
- `OpenAI compatible provider <name> not found`: add or fix the `openai_compatible_providers` record.
- `has no base URL`: add `base_url` to that provider record.
- LiteLLM base URL errors: ensure the endpoint includes the provider's OpenAI-compatible path when required, commonly a `/v1` suffix.

### 2. `user_model_registry`

New user models use `model_name="user_model::<entry_id>"`. Registry entries have:

```python
{
    "id": "my-local-model",
    "provider_type": "custom",     # or "builtin"
    "provider_id": "local-vllm",    # custom provider name, or ModelProviderName value for builtin
    "model_id": "meta-llama/Llama-3.1-8B-Instruct",
    "name": "Local Llama",
    "overrides": {
        "supports_structured_output": False,
        "structured_output_mode": "json_instructions"
    },
}
```

For `provider_type="custom"`, `core_provider(...)` maps the run to `openai_compatible` and carries `openai_compatible_provider_name`. For `provider_type="builtin"`, `provider_id` must be a valid `ModelProviderName` value. Overrides are filtered to valid `KilnModelProvider` fields; unknown override keys are ignored for forward compatibility.

### 3. Legacy `custom_models`

Legacy `custom_models` are stored as `provider::model_id` strings and run through `kiln_custom_registry`. Preserve the exact slug format because historical run matching depends on it.

## Structured output modes

`StructuredOutputMode` controls how the adapter asks the model for JSON and how it validates the result.

| Mode | Adapter behavior | Good fit | Common failure |
|---|---|---|---|
| `json_schema` | Sends API `response_format` with `type=json_schema` and schema name `task_response`. | Providers/models with real JSON schema support. | Provider rejects schema features; adapter strips numeric bounds but provider may reject other schema details. |
| `function_calling` | Forces a strict `task_response` function/tool call using the output schema. | Models with strong tool/function calling and no other runtime tools. | Conflicts with normal tools because both would occupy the `tools` response-format path. |
| `function_calling_weak` | Same function-call path with `strict=False`. | Providers that reject strict tool schemas. | Weaker schema enforcement from provider. |
| `json_mode` | Sends API `response_format={"type":"json_object"}`. | Models that can produce JSON but do not accept full schema. | Output is valid JSON but may not match task schema. |
| `json_instructions` | Adds schema instructions to prompt only; no API response format. | Custom/OpenAI-compatible or untested models. | Model returns prose, fenced JSON, or wrong schema. |
| `json_instruction_and_object` | Adds prompt instructions and requests `json_object`. | Models with JSON mode but poor schema adherence. | Still requires post-hoc schema validation. |
| `json_custom_instructions` | Assumes prompt already contains JSON instructions. | Carefully authored saved prompts. | Missing prompt instructions causes unstructured output. |
| `default` | Adapter chooses a fallback; Ollama/Docker Model Runner use JSON schema, most others use function calling, OpenAI strict by default. | Legacy configs. | Less explicit and harder to debug. |
| `unknown` | Upgraded at adapter init using the registry's default mode when possible. | Older persisted run configs. | If still unknown, adapter raises. |

Structured task outputs are always validated after model/tool return. If the parsed output is not a dict or does not satisfy `Task.output_json_schema`, the run fails even when the provider accepted the request.

## Thinking levels

`thinking_level` is a string on `KilnAgentRunConfigProperties`. It is validated only for non-empty text. Semantic validity is determined by the resolved model provider entry.

Rules:

- If `thinking_level` is explicitly present on the run config, the adapter uses it.
- If it is not present, the adapter may use the provider's `default_thinking_level`.
- If the provider has no `available_thinking_levels`, stale `thinking_level` values are ignored.
- OpenRouter models may receive either `reasoning_effort=<level>` or `reasoning={"effort": <level>}` depending on provider flags.
- Anthropic native `thinking_level="none"` is omitted rather than sent as `reasoning_effort="none"`.
- Some Anthropic models request summarized thinking display so reasoning text is returned.
- Some Gemini entries enable reasoning with `reasoning={"enabled": True}`.
- Some SiliconFlow models use `enable_thinking` boolean flags.
- Reasoning-capable models may require reasoning in `intermediate_outputs["reasoning"]`; if no reasoning is returned and the model does not mark it optional for structured output, the adapter raises.

Use the registry inspection script to see which provider entries expose `available_thinking_levels` and defaults for a selected provider.

## Sampling parameter caveat

Some provider entries set `temp_top_p_exclusive=True`. For these models, the adapter removes default `temperature=1.0` or `top_p=1.0` but raises if both are customized:

```text
top_p and temperature can not both have custom values for this model.
```

Recovery: leave one of them at `1.0` or unset it in the UI/config path.

## Boundary notes

- Model-provider selection and adapter behavior are covered here.
- Persisting provider choices inside projects, saved run configs, prompts, or exported packages belongs to project-datamodel.
- Fine-tune creation, provider job status, fine-tune datasets, and prompt optimization belong to evals-optimization-finetuning.
- Provider settings APIs and UI forms belong to server-desktop-web-api.
- Embedding/reranker model lists are mentioned here for registry orientation; RAG setup and indexing belong to rag-documents-data.

## Evidence notes

Repo-relative source evidence: `libs/core/kiln_ai/adapters/ml_model_list.py`, `libs/core/kiln_ai/adapters/ml_embedding_model_list.py`, `libs/core/kiln_ai/adapters/reranker_list.py`, `libs/core/kiln_ai/adapters/provider_tools.py`, `libs/core/kiln_ai/adapters/user_model_entry.py`, `libs/core/kiln_ai/utils/litellm.py`, `libs/core/kiln_ai/utils/config.py`, `libs/core/kiln_ai/datamodel/datamodel_enums.py`, and provider/adapter tests.
