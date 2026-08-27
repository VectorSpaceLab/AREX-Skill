# Chat and Model Troubleshooting

## Model does not appear

- **Symptom**: the chat UI does not list the model the user expects.
- **Likely causes**: wrong provider URL, provider API key missing, access control excludes the model, or the backend has not refreshed the provider list.
- **Recovery**: verify the provider settings, then check the model access configuration and any fallback rules.

## `Model not found`

- **Symptom**: the backend reports that a requested model was not found.
- **Likely causes**: the model name is not valid for the selected provider, or a provider prefix was stripped incorrectly.
- **Recovery**: compare the visible model name in the UI with the backend provider's expected identifier.

## `Provider not configured`

- **Symptom**: a provider-specific workflow says the provider is not configured.
- **Likely causes**: the API key or base URL is absent, or the provider was never enabled.
- **Recovery**: fill in the provider settings and retry the chat path from the playground first.

## `Access prohibited`

- **Symptom**: the user can see the UI but cannot use a model.
- **Likely causes**: model access rules, group restrictions, or admin policy blocks the route.
- **Recovery**: check access control before assuming the backend is broken.

## Slow or stalled responses

- **Symptom**: the model begins responding but stalls, times out, or streams poorly.
- **Likely causes**: upstream timeout settings, slow provider latency, or the wrong pass-through mode.
- **Recovery**: compare the provider timeout settings with the expected response time and retry with a smaller prompt in the playground.

## Prompt behaves differently than expected

- **Symptom**: the same prompt produces a different response in Open WebUI than in a direct provider test.
- **Likely causes**: prompt normalization, system-message injection, or chat-variable handling.
- **Recovery**: inspect the normalized prompt path instead of changing the provider immediately.

## Safe checks to repeat

- `open-webui --help`
- `python -I -c "from importlib.metadata import version; print(version('open-webui'))"`
- A tiny playground prompt after fixing provider settings
