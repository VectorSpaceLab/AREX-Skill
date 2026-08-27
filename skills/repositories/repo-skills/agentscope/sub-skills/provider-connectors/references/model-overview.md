# Model Overview

## Purpose

Read this when you need the chat-model side of AgentScope: provider classes, credential shapes, model defaults, and the parameter surface that the tests exercise.

## Verified chat model families

| Class | Credential | Verified defaults / notes |
| --- | --- | --- |
| `OpenAIChatModel` | `OpenAICredential(api_key=...)` | `stream=True`, `context_size=128000`, `max_retries=3`, optional `extra_body` |
| `DashScopeChatModel` | `DashScopeCredential(api_key=...)` | `stream=True`, `context_size=131072`, `max_retries=3`, supports `Parameters(max_tokens, thinking_enable, thinking_budget)` |
| `GeminiChatModel` | `GeminiCredential(api_key=...)` | `stream=True`, `context_size=1048576`, `max_retries=3` |
| `OllamaChatModel` | `OllamaCredential(...)` or none | `stream=True`, `context_size=32768`, local-server flow |
| `AnthropicChatModel` | `AnthropicCredential(api_key=...)` | `stream=True`, `context_size=200000`, `max_retries=3` |
| `MoonshotChatModel` | `MoonshotCredential(api_key=...)` | `stream=True`, `context_size=131072`, `max_retries=3` |
| `XAIChatModel` | `XAICredential(api_key=...)` | `stream=True`, `context_size=131072`, `max_retries=3`, default formatter is `XAIChatFormatter` |
| `OpenAIResponseModel` | `OpenAICredential(api_key=...)` | `stream=True`, `context_size=200000`, `max_retries=3` |
| `DeepSeekChatModel` | `DeepSeekCredential(api_key=...)` | Exported from `agentscope.model`; see the unit tests for its mocked API contract. |

## Credential shapes

The verified credential constructors are:

- `OpenAICredential(api_key, organization=None, base_url=None)`
- `DashScopeCredential(api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')`
- `GeminiCredential(api_key)`
- `OllamaCredential(host=None)`
- `XAICredential(api_key, api_host='api.x.ai')`
- `AnthropicCredential(api_key, base_url=None)`
- `DeepSeekCredential(api_key, base_url='https://api.deepseek.com')`
- `MoonshotCredential(api_key, base_url='https://api.moonshot.cn/v1')`

## Practical notes

- The provider unit tests mock the network calls, so a failed import is usually an environment or extra problem rather than a live API problem.
- `XAIChatFormatter` defaults to `['text/plain', 'image/jpeg', 'image/png']` input types, which is a useful hint when a multimodal request gets rejected.
- `OpenAIChatModel` and `OpenAIResponseModel` have different API shapes even though they share the same credential class.
- For provider matrix checks, prefer the bundled `scripts/provider_matrix.py` rather than a live network call.

## When to use this reference

- Before choosing the provider class for an agent.
- When a chat provider imports but the request shape or credential class is wrong.
- When a test is mocking one provider family and you need to compare it to another.
