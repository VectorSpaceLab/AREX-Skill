# Provider Matrix

| Executor | Reviewer route | Typical registration/config | Independence | Main caution |
| --- | --- | --- | --- | --- |
| Claude Code | Codex MCP | Register `codex` with Codex MCP server; authenticate Codex | Cross-family | Restart Claude Code after registration; keep the server name expected by ARIS skills. |
| Codex CLI | Claude-review MCP | Register `claude-review` in Codex MCP config; ensure Claude CLI is available | Cross-family | Check CLI path, timeout, and model override. |
| Codex CLI | Gemini-review MCP | Register `gemini-review`; choose API or CLI backend and set Gemini credentials | Cross-family | API/CLI backend selection changes env vars and failure modes. |
| Claude or Codex | Generic `llm-chat` | Set `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, optional fallback, then register MCP | Depends on chosen model family | OpenAI-compatible schema must match; 504 fallback is not a correctness guarantee. |
| Claude Code | MiniMax MCP | Set `MINIMAX_API_KEY`, optional base URL/model, register `minimax-chat` | Usually cross-family | Temperature is clamped to MiniMax-supported range; missing keys should be explicit. |
| Claude Code | Manual review | Register `manual-review`; choose browser or file mode and pending directory | Human independent review | Local HTTP/file handoff can block until a response arrives; preserve token and timeout state. |
| Claude Code | Feishu/Lark bridge | Set Feishu app/user credentials; install `lark-oapi`; run bridge | Human/channel dependent | Optional only; live credentials and package are required. |
| Claude Code | Codex image bridge | Use Codex app-server bridge for image/figure operations | Provider-specific | Optional; separate from text review and may require local Codex runtime. |

## Cross-Model Rule

ARIS's provenance helper classifies model families and fails closed on unknown or colliding names. A same-family pair (for example Codex executor plus GPT/Codex reviewer, or Claude executor plus Claude reviewer) is not independent acceptance. Codex base review can be useful but should remain provisional unless another gate accepts it.

## Credential Hygiene

- Keep keys in environment variables or host-managed secret stores.
- Redact keys and bearer tokens from error logs and review artifacts.
- Keep model names and endpoint URLs in project configuration only when they are safe to publish.
- Record provider availability and skips explicitly in workflow reports.
