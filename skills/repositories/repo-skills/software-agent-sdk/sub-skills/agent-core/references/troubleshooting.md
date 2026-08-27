# Agent Core Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Conversation never starts | Missing credentials, wrong model, or workspace path that does not exist. | Verify `LLM_API_KEY`, model string, and workspace path before building the agent. |
| Conversation pauses unexpectedly | Stuck detection or interrupts triggered. | Inspect the run status, review callbacks, and raise limits only when the task is genuinely long-running. |
| Remote title generation still works but the deprecated route is mentioned | Old guidance or stale notes. | Use the shared title helper path documented here; do not depend on removed transport-only title routes. |
| Unexpected model/provider behavior | Ambiguous provider inference or stale model selection. | Construct a new `LLM` for a changed provider/model and keep provider-specific logic out of higher-level code. |
| Conversation history errors during Anthropic-style tool use | Malformed tool-use/tool-result history. | Let the SDK's malformed-history recovery and condensation path handle it; do not convert it into a generic context overflow diagnosis. |
