# Provider and Framework Recipes

## Direct clients

| Provider | Typical pattern | Notes |
| --- | --- | --- |
| OpenAI | `mem.llm.register(client=openai_client)` | direct client path, can also be used with OpenAI-compatible base URLs |
| Anthropic | `mem.llm.register(client=anthropic_client)` | direct client path |
| Google | `mem.llm.register(client=google_client)` | direct client path |
| xAI | `mem.llm.register(client=xai_client)` | direct client path |

## Framework models

| Framework | Named args | Notes |
| --- | --- | --- |
| Agno | `openai_chat=...`, `claude=...`, `gemini=...`, `xai=...` | choose one framework family per call |
| LangChain | `chatbedrock=...`, `chatgooglegenai=...`, `chatopenai=...`, `chatvertexai=...` | LangChain model objects must use named args, not `client=` |
| PydanticAI | provider-specific direct-client wrappers in the package | use the unified registration route when the SDK object matches a supported wrapper |

## OpenAI-compatible reminder

If the user is pointing an OpenAI client at a compatible endpoint, keep the
request on the direct OpenAI path and explain any platform-label caveats rather
than treating it as an unsupported provider by default.

## Selection rule

- Use the direct client path when the SDK object is already instantiated.
- Use a framework named argument when the client object is coming from Agno or
  LangChain.
- If the user wants a generic provider router, send them to the cloud/gateway
  skill instead; Memori is the memory layer, not a gateway.
