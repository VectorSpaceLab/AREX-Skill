# Agent tools and providers troubleshooting

Use the returned error text and logs to choose one corrective action. Do not
retry a failed network or CLI operation indefinitely, and never copy secrets
into a report while diagnosing.

| Symptom | Likely cause | Safe response |
|---|---|---|
| `Unknown provider ...` | Misspelled provider or unsupported label | Use exactly `anthropic`, `openai`, `claude_cli`, `codex_cli`, or one of the documented domestic preset aliases. |
| Domestic preset uses wrong endpoint | Explicit `base_url` or `api_key_env` was not actually passed, or contains only whitespace | Verify the normalized non-secret config. Explicit nonblank values override the preset; otherwise use the preset table. |
| SDK reports missing API key | `api_key_env` is empty/unset, or the named variable is absent | Export the named variable in the process environment or pass a direct key only to a programmatic constructor. Never log the value. |
| Anthropic-compatible endpoint rejects auth | Wrong auth mode or endpoint | `auth_token`/`auth_token_env` is supported by the Anthropic client path; OpenAI-compatible paths use `api_key` and do not pass `auth_token`. Confirm the provider contract with the endpoint owner. |
| Model unexpectedly changes on OpenAI call | An Anthropic provider fell back to OpenAI because `anthropic` is unavailable | Install/use the intended SDK or set `provider: openai` with the endpoint's model. Cross-provider aliases are mapped only when `self.provider != "openai"`. |
| API package missing | Optional SDK is not installed | Anthropic logs and tries OpenAI; OpenAI logs and returns `{"action":"wait","reason":"LLM not available"}`. Install the required SDK in the runtime rather than treating mock output as research evidence. |
| `claude_cli` cannot perform a requested tool | CLI missing, not logged in, timed out, or exited nonzero | Check CLI availability/login outside the worker flow. The dispatcher returns a wait JSON on these failures. Its `--tools ""` setting is intentional. |
| Codex worker summary has no PID/log | `codex_cli` ran its own internal tools and bypassed the registry | Treat the handoff as non-authoritative. Use `claude_cli`, `anthropic`, or `openai` for workers, especially `code` workers that launch experiments. |
| Worker loops until max turns | Model keeps emitting calls or the tool result is not actionable | Inspect the returned `<tool_result>`, correct the next call, or stop. The hard ceiling is 12/40/30 for idea/code/writing; do not raise it blindly. |
| Fenced example changed a file | A caller executed the example outside the dispatcher or used a different parser | Keep multiline illustrative calls inside fences and execute only `_parse_tool_calls` survivors. Test with a fake registry before enabling writes. |
| Expected call was ignored | Call is fenced, malformed JSON, or has no truthy `name` | Emit a top-level JSON-object call with exact tags. Do not rely on prose or a one-line fence as a real protocol call. |
| `args must be a JSON object` | Model emitted a string/list/null-like non-dict args value | Re-emit `args` as an object, or omit it when the tool has no arguments. The dispatcher must not expand it as `**args`. |
| `Unknown tool: ...` | Tool is not in the registry or not in this worker's allow-list | Select from `get_tools_for(agent_type)`. Do not grant an unrelated tool by editing the prompt only. |
| `Path cannot be empty` | Blank path | Supply a workspace-relative path. |
| `Path must be relative to workspace` | Absolute path supplied | Use a path relative to the configured workspace; do not use `/etc/...`, `~`, or a host absolute path. |
| `Path escapes workspace` | `..` component or resolved symlink exits the root | Choose an in-workspace path. Do not weaken normalization or follow symlinks. |
| `Cannot overwrite protected file` | Write targeted `state.json`, `MEMORY_LOG.md`, `PROJECT_BRIEF.md`, or `.lock` | Read it if needed, but use the owning lifecycle/memory mechanism for updates. |
| Search returns no expected file | File is hidden in a skipped directory, symlinked, binary, unreadable, or over 2 MB | Read a known in-workspace text file directly or narrow the path; do not assume no match means no code exists. |
| `Invalid search pattern` | Regex syntax is invalid | Validate/escape the regex and rerun with a bounded result count. |
| Semicolon payload only echoes text | Expected behavior for non-shell invocation | Keep it that way. The backend receives argv, not shell syntax; verify no injected file exists. Do not change to `shell=True`. |
| Command is blocked | Executable basename is on the deny-list | Use a safe, purpose-specific command. Never bypass the block by invoking a destructive command through an untrusted shell. |
| Shell metacharacters still have effect | Command explicitly invoked `sh`, `bash`, `python`, or another interpreter | This registry is not a complete privilege sandbox. Stop, narrow the command, and use a controlled execution/backend policy. |
| `Search failed: ...` | Semantic Scholar network, rate limit, or decode error | Surface the error, wait for permission/backoff, or use an already available source. Do not claim literature results from an error object. |
| `arXiv search failed: ...` | arXiv network/API failure | Surface the error and retry later only with bounded backoff. A successful HTTP response with malformed Atom XML becomes a generic structured tool error. |
| `get_paper failed: ...` | Invalid ID for upstream API, network, or decode failure | Check the identifier form (`arXiv:`, `DOI:`, `CorpusId:`, or provider ID) and keep reference/citation expansion bounded. Blank IDs fail locally. |

## No-side-effect diagnostic procedure

1. Run the bundled provider validator with a provider, model, and optional
   non-secret endpoint/key-environment names.
2. Feed a fake parser/registry the fenced illustrative call, traversal path,
   and semicolon command. Confirm fenced calls are absent, traversal returns a
   JSON error, and the semicolon remains an argument rather than shell syntax.
3. Only after those checks, configure a real provider. For literature tools,
   obtain explicit network permission and preserve the bounded timeout/error
   behavior.
4. For a code worker, accept a PID/log only from a valid registry launch result;
   if `codex_cli` was used, route the launch again through a registry-capable
   provider before monitoring.
