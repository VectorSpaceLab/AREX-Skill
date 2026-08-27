# LLM Registration API

## Unified entry point

```python
mem.llm.register(
    client=None,
    openai_chat=None,
    claude=None,
    gemini=None,
    xai=None,
    chatbedrock=None,
    chatgooglegenai=None,
    chatopenai=None,
    chatvertexai=None,
)
```

## Routing rules

- `client=` is for direct SDK clients.
- The named arguments are for framework-specific models.
- Do not mix `client=` with any named framework argument.
- Do not mix Agno and LangChain named arguments in the same call.

## Supported routes

- Direct clients: OpenAI, Anthropic, Google, xAI, and other supported wrappers
  that match the installed client adapters.
- Agno models: `openai_chat`, `claude`, `gemini`, `xai`.
- LangChain models: `chatbedrock`, `chatgooglegenai`, `chatopenai`,
  `chatvertexai`.

## Common error messages

- `Cannot mix direct client registration with framework registration`
- `Cannot register both Agno and LangChain clients in the same call`
- LangChain helper error: use named parameters such as `chatopenai=client`
  instead of `client=...`
- `UnsupportedLLMProviderError` for unsupported clients or provider names

## Deprecated accessors

The older `memori.agno.register(...)`, `memori.openai.register(...)`,
`memori.anthropic.register(...)`, `memori.google.register(...)`,
`memori.langchain.register(...)`, `memori.pydantic_ai.register(...)`, and
`memori.xai.register(...)` accessors remain visible in source for compatibility,
but the unified `mem.llm.register(...)` path is the preferred route.

## Practical rule

If the user knows the SDK class, use the direct path. If the user already has a
framework model object, use the named framework argument that matches the model
family.
