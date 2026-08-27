# Python SDK troubleshooting

Use this reference when the task is about recovery, diagnosis, or narrowing a failing Python SDK surface.

## 1. Editable install or import failures

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| `import strands` fails | The package is not installed in the interpreter you are using, or the import is coming from the wrong environment | Run `scripts/python-core-check.sh`; confirm the same `python` sees the package before you run pytest |
| `from strands import Agent, tool` fails | A stale editable install or a mismatched checkout is shadowing the package | Reinstall the package in editable mode from the checkout, then re-run the core check |
| Signature checks fail immediately | You are running against a different package version than the one the skill was distilled from | Rebuild the environment, then rerun the bundled core check before editing deeper code |

Recovery pattern:

1. Use the bundled core check first.
2. Make sure the checkout you are editing is the one the interpreter can import.
3. If you are inside `strands-py/`, reinstall the package in editable mode for that checkout and rerun the import check.

## 2. Missing provider extras

The most common cause of provider import failures is a missing extra rather than a broken code path.

| Provider | Extra |
| --- | --- |
| Anthropic | `anthropic` |
| Gemini | `gemini` |
| LiteLLM | `litellm` plus `openai` |
| LlamaAPI | `llamaapi` |
| Mistral | `mistral` |
| Ollama | `ollama` |
| OpenAI | `openai` |
| SageMaker | `sagemaker` |
| Writer | `writer` |
| Bidirectional streaming | `bidi`, `bidi-io`, `bidi-gemini`, or `bidi-openai` |
| Docs generation | `docs` |
| Cedar integrations | `cedar` |

What to do:

- Install only the extra you need.
- Do not install `all` unless the task truly spans many providers.
- Treat provider-backed tests as optional unless the task explicitly requires them and credentials are available.

## 3. Malformed tool schemas or `@tool` misuse

Common causes:

- A manual `name` change that no longer matches the wrapped function.
- Missing `description` or `inputSchema` on a custom tool spec.
- A `ToolContext` parameter without `@tool(context=True)`.
- A `context` parameter name mismatch.
- Unsupported `Annotated[..., Field(...)]` usage in the decorator path.
- JSON-serialization failures in tool return values.

Recovery steps:

- Re-read the `tool` contract in `api-reference.md`.
- Run `tests/strands/tools/test_decorator.py` for the exact failure mode.
- Keep `tool_spec` changes narrow and preserve the tool name identity.
- If you need a context parameter, use the supported `ToolContext` injection path instead of inventing a new calling convention.

## 4. MCP client config or transport errors

Common symptoms:

- `MCPClientInitializationError`
- `CLIENT_SESSION_NOT_RUNNING_ERROR_MESSAGE`
- A client that never finishes startup
- A server config that silently does nothing
- Task-augmented execution not activating

Likely causes:

- `MCPClient` used outside its context manager.
- A malformed `load_servers` config shape.
- A transport mismatch between `command` and `url`.
- Missing env vars or path interpolation failures.
- `continue_on_error` swallowing an individual server failure.
- A task-support feature used without opt-in or without server support.

Recovery steps:

- Recheck whether the client is entered with `with MCPClient(...) as client:`.
- Validate the config shape and the transport choice.
- Check `startup_timeout` before assuming the server is hung.
- Confirm whether the server failure is expected to be swallowed by `continue_on_error`.
- For task support, verify both client opt-in and server/tool task capability.
- Use `tests/strands/tools/mcp/test_mcp_client.py` for lifecycle failures and `test_mcp_client_tasks.py` for task behavior.

## 5. Context manager surprises

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| A stateful model rejects a conversation manager | Stateful providers manage conversation state server-side | Let the model manage state, or remove the conversation-manager setting |
| Context management seems non-durable | `context_manager="auto"` uses in-memory offloading defaults | Provide explicit durable storage through the plugin path when you need persistence across restarts |
| The agent’s context behavior changes after switching to `agentic` | `agentic` mode adds model-driven context tools and uses a different summarization posture | Re-check the intended mode and the matching tests before changing behavior |

## 6. Memory or session credentials and configuration

Common causes:

- A memory store is not writable but is being asked to accept writes.
- A store exposes no `add` or `add_messages` sink, so extraction cannot write anywhere.
- A search/add tool is scoped to a store name that does not exist.
- S3-backed persistence needs AWS credentials or a valid region/bucket.
- A snapshot manager is being used as if it were a full multi-agent session store.

Recovery steps:

- Recheck the store protocol and the `MemoryManager` constructor contract.
- Use `tests/strands/memory/test_memory_manager.py` to isolate store-scoping and extraction behavior.
- For S3-backed paths, treat credentials as required inputs, not optional hints.
- For snapshot workflows, remember that the manager stores one agent snapshot at a time and does not replace every persistence need.

## 7. Sandbox path, timeout, and shell issues

Likely causes:

- Invalid environment variable names for shell-backed backends.
- A backend implementation ignoring `timeout`, `cwd`, or `env`.
- A path that does not exist on the remote backend.
- A command string that is valid locally but not on the target shell.

Recovery steps:

- Check whether the concrete sandbox backend honors the abstract `Sandbox` contract.
- Use valid POSIX environment-variable names.
- Recheck whether the backend is Docker, SSH, or host-default and verify its path semantics.
- Treat the host-default sandbox as non-isolated.

## 8. Provider error translation

Likely cause: the provider is surfacing raw vendor errors instead of SDK exceptions.

What the SDK expects:

- Context-window overflow becomes `ContextWindowOverflowException`.
- Throttling or rate-limit behavior becomes `ModelThrottledException`.
- The original exception should be chained with `from`.

Recovery steps:

- Reuse the existing provider error-mapping pattern.
- Add or update a provider-specific test for the translated exception type.
- Do not let the vendor error escape unchanged when the SDK already has a typed equivalent.

## 9. Async/sync misuse

Common mistakes:

- Calling `Agent.invoke_async` or `stream_async` from sync code without awaiting them.
- Using `Agent.__call__` in async code when the task should stay in the async path.
- Treating `tool.stream(...)` as a regular function instead of an async generator.
- Expecting `structured_output()` to be the preferred public path for new work.

Recovery steps:

- Use the async API in async code and the sync wrapper only when you need a blocking call.
- Await tool streams and model streams explicitly.
- Re-run the bundled core check, then the smallest relevant pytest slice.

## 10. When the bundled checks pass but behavior still looks wrong

- Compare the task against the verified API facts in `api-reference.md`.
- Re-read the closest unit test before widening your edit.
- If the task touches a public surface, inspect the file being edited plus the nearest test module only.
- Keep provider-backed or live-network paths out of the default recovery path unless the task explicitly depends on them.
