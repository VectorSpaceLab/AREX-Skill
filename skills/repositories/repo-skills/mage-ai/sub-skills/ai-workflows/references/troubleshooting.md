# AI workflows troubleshooting

## Common failures

### `AI Mode is not available`
- Confirm the repo's AI config selects a supported mode.
- Make sure the relevant build flag and client path are available.
- Use the bundled config check script before trying a live generation request.

### OpenAI generation fails immediately
- Confirm the API key is present in the repo config or the environment.
- Check that the OpenAI helper path is the one selected by `AIConfig.mode`.
- If the model returns invalid JSON, the helper may fail to parse the response.

### Hugging Face generation fails immediately
- Confirm both the endpoint and the API token are set.
- Make sure the inference endpoint is running and reachable.

### Generated output is malformed
- The workflow expects structured prompts and structured responses.
- Retry with a smaller, more specific prompt.

### The user asked for a generation feature but the environment is offline
- AI generation is an external side effect.
- Switch to a config-only or documentation-only workflow until the credentials and network path are available.
