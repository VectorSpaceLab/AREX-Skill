# Chat and Model Workflows

## Typical flow

1. Start Open WebUI from the `deployment` sub-skill.
2. Configure a provider or backend URL in the UI or environment.
3. Pick a model in the chat or playground view.
4. Send a short test prompt.
5. Adjust routing, fallback, or access control if the model does not appear or the response does not stream correctly.

## Provider patterns

### Ollama

- Set `OLLAMA_BASE_URL` to the reachable Ollama server.
- Use the app's model list and chat UI to confirm that the backend responds.
- If the model is missing, check the URL, the network path, and any access-control settings.

### OpenAI-compatible providers

- Use the provider's API key and base URL.
- Verify whether passthrough or rewriting is enabled.
- If a model name is accepted by the provider but not shown in Open WebUI, check model access rules and any fallback configuration.

### Fallback and passthrough

- `ENABLE_OPENAI_API_PASSTHROUGH` controls whether traffic is forwarded without rewriting.
- `ENABLE_CUSTOM_MODEL_FALLBACK` can make a missing model path recover differently.
- Treat these as routing decisions, not generic startup settings.

## Prompt and message flow

- Prompt variables are normalized in the backend before the model call.
- Chat state, response streaming, and follow-up generation are part of the core conversation flow.
- If a prompt behaves oddly, compare the UI prompt with the normalized backend input rather than assuming the provider is at fault.

## Playground and evaluation

- Use the playground for quick model and prompt checks without a long chat history.
- Use evaluation-oriented routes only when the user explicitly asks about comparison or assessment.

## Common configuration flags

- `OLLAMA_BASE_URL`
- `ENABLE_OPENAI_API_PASSTHROUGH`
- `ENABLE_CUSTOM_MODEL_FALLBACK`
- `AIOHTTP_CLIENT_TIMEOUT` and related upstream timeout settings
- Provider-specific API key variables

## Good diagnostic questions

- Which provider is selected?
- Which model name is actually visible to the backend?
- Is the response failing before the request reaches the provider, or after?
- Is the problem the prompt, the route, the model name, or the upstream service?
