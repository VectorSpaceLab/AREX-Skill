# Provider and Operations Reference

## Provider families seen in the repository

- OpenAI
- Anthropic
- Vertex / Gemini
- Azure variants
- Ollama
- LM Studio
- Tavily and other search/web helpers when enabled by config

## Operations topics

- logging and maintenance cookbook flows
- MCP integration and user tools
- full-mode orchestration dependencies
- provider key configuration and validation

## Practical guidance

- Pick the smallest config that satisfies the user's provider needs.
- Do not assume every provider is available in every environment.
- Keep secrets out of examples and use env-var names instead of literal values.
