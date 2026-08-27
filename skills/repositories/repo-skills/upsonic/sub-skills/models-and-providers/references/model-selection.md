# Model Selection Notes

## What future agents should ask first

1. Which provider family does the user want: OpenAI, Anthropic, Google, Bedrock, Groq, Cohere, OpenRouter, local, or gateway?
2. Does the task need tools, JSON schema output, images, or just a plain text response?
3. Is the user already pinned to a provider/model name in code or an environment variable?

## Selection guidance

| Situation | Guidance |
| --- | --- |
| User names a provider family | Route straight to the matching `provider/model` form. |
| User provides a bare model name | Normalize to a provider-prefixed form and warn that bare names are deprecated. |
| User wants local or self-hosted models | Check provider-specific support such as Ollama, LM Studio, VLLM, or similar backends. |
| User wants structured output | Choose a model/profile that advertises the needed output mode. |
| User wants the fewest moving parts | Keep the model choice in `Agent` or `Direct`; do not mix in memory or tools until the provider is stable. |

## Example strings

- `openai/gpt-4o`
- `anthropic/claude-sonnet-4-6`
- `google/gemini-2.5-flash`
- `gateway/anthropic/claude-sonnet-4-6`
- `bedrock/us.anthropic.claude-sonnet-4-6`

If the user asks for the exact supported model list, use the bundled registry script instead of hand-maintaining a partial list.
