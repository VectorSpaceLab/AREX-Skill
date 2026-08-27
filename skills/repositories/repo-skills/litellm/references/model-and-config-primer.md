# LiteLLM Model and Config Primer

## Model Names

LiteLLM uses OpenAI-format requests with model strings that usually encode the provider. Common shapes include:

- `openai/gpt-4o` for OpenAI models.
- `anthropic/claude-sonnet-4-20250514` for Anthropic models.
- `azure/<deployment-name>` or proxy model aliases for Azure OpenAI deployments.
- Proxy model groups such as `gpt-4o` when the proxy or `Router` maps that alias to one or more deployments.
- Agent routes such as `a2a/<agent-name>` when the proxy exposes A2A agents.

When a task fails with provider selection errors, check the model prefix, `custom_llm_provider`, `api_base`/`base_url`, `api_version`, and whether the model is a direct provider model or a proxy/router alias.

## Credentials

Provider credentials normally come from environment variables or explicit call parameters. Do not hard-code keys in generated examples, config files, curl commands, or scripts. Use placeholders such as `os.environ["OPENAI_API_KEY"]`, `ANTHROPIC_API_KEY`, `AZURE_API_KEY`, or `LITELLM_MASTER_KEY`.

For proxy traffic, distinguish provider credentials used by the proxy from virtual keys used by callers. A client request to the proxy typically uses `Authorization: Bearer <virtual-key>` while the proxy config or secret manager holds provider credentials.

## SDK Parameter Conventions

LiteLLM’s SDK accepts OpenAI-style parameters such as `messages`, `stream`, `temperature`, `max_tokens`, `max_completion_tokens`, `tools`, `tool_choice`, `response_format`, `extra_headers`, `api_key`, `api_base`/`base_url`, and `api_version`. Unsupported provider parameters may be dropped or require provider-specific kwargs. Check provider endpoint support before assuming every OpenAI parameter works for every backend.

## Proxy YAML Conventions

A minimal proxy config usually has:

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY

litellm_settings:
  set_verbose: false

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

Routing policy, retries, budgets, guardrails, callbacks, spend tracking, and pass-through routes add fields under `router_settings`, `litellm_settings`, `general_settings`, or feature-specific blocks. Keep config changes minimal and validate model groups before starting long-running services.

## Choosing the Right Surface

- Use direct SDK calls for application code that can manage provider keys locally.
- Use the proxy when teams need centralized auth, virtual keys, spend tracking, guardrails, shared model aliases, or OpenAI-compatible HTTP access.
- Use `Router` directly when Python code needs load balancing/fallback without operating a proxy service.
- Use pass-through routes only when LiteLLM should forward provider-specific APIs that are not covered by the normal OpenAI-compatible endpoint family.
