# Text tool-use protocol

The worker interface is provider-agnostic. API SDK calls do not use a native
tool schema, and CLI providers are text oracles. The dispatcher appends plain
text tool instructions and recognizes only this form:

```text
<tool_call>
{"name": "read_file", "args": {"path": "config.yaml"}}
</tool_call>
```

The model has no direct filesystem, shell, or network access through the worker
prompt. A call is a request to the dispatcher, not an instruction to execute
arbitrary text.

## Parsing rules

The parser applies these rules in order:

1. Remove every multiline triple-backtick block, including an optional language
   tag, before searching for calls. This suppresses fenced illustrative calls.
2. Find `<tool_call>` blocks with a JSON object body, allowing whitespace and
   newlines. Bodies are parsed with `json.loads`.
3. Skip malformed JSON with a warning; do not terminate the worker.
4. Keep only parsed dictionaries with a truthy `name`. A missing `args` field
   is allowed and behaves as `{}`. A non-dictionary `args` value is not sent to
   the registry; it yields a structured ``args must be a JSON object`` result.
5. Preserve source order, including multiple calls in one model response.

A response with no surviving calls is a final worker response. Do not execute
XML-like tags found in prose, quoted examples, or a fenced code block. The
fence suppressor is intentionally designed for the common multiline Markdown
example; callers should still instruct providers to emit real calls at top
level and never in fences.

## One worker turn

`dispatch_worker` starts with one user message containing the task. It renders
the worker's exact schemas into the system prompt, then repeats:

1. Call the configured provider.
2. Parse all top-level calls.
3. If there are none, return the response as the final answer.
4. Append the assistant response unchanged to history.
5. Execute each call sequentially through `tool_registry.execute_tool(name,
   args)`.
6. Append one user message containing one result block per call:

```text
<tool_result name="read_file">
<tool output, often JSON or file text>
</tool_result>
```

7. Call the provider again with the expanded history.

All tool exceptions are converted at the registry boundary to a JSON error.
The dispatcher also handles a non-dict `args` value before the registry, so a
model cannot cause a Python `**args` expansion failure. An unknown tool name
returns `{"error":"Unknown tool: <name>"}`.

The loop is bounded by worker configuration: `idea` 12 turns, `code` 40, and
`writing` 30. When the last allowed turn still contains a call, the dispatcher
logs a max-turn warning and returns that last response with the calls already
executed. There is no implicit retry beyond the ceiling.

## Authoritative launch handoff

A code worker's result initially includes `agent` and final `response`, and
includes `tool_calls` when calls occurred. The parser then searches the tool
result log from newest to oldest for `launch_experiment`. If that result is
valid JSON with a non-null `pid`, it sets:

```json
{
  "experiment_launched": true,
  "pid": 4321,
  "log_file": "logs/exp.log"
}
```

The tool result wins even if the model's prose claims another PID. Monitoring
must consume this structured result; it must not scrape or trust a prose PID
when the registry supplied one. If no usable launch result exists, legacy
fallback may mark a code response as launched when prose contains `PID` or
`launched`, and may scrape `PID=123`; that fallback is non-authoritative and
may have no log path.

This distinction is especially important with `codex_cli`: Codex can run
built-in tools outside the registry and return a summary without a registry
launch result. Do not use a codex worker response as proof that a process was
launched or as a source of an authoritative PID/log path.

## Provider-specific prompt transport

The Anthropic and OpenAI paths send structured role/content messages to their
SDK APIs, but the tool instructions remain text. `claude_cli` serializes the
system and message history with `===== SYSTEM =====`, `===== USER =====`, and
`===== ASSISTANT =====` markers and sends it over stdin with `--tools ""`; its
built-in tools are disabled. `codex_cli` serializes the same markers but uses
`codex exec`, whose built-in agentic loop cannot be disabled.

The rendered tool section explicitly says that the worker has no direct
filesystem, shell, or network access, gives a top-level example, permits
multiple blocks, and requires a plain response with no calls to finish. Keep
those instructions intact when adapting prompts.

## Synthetic protocol checks

A safe parser review should include all of these without a real registry:

- a fenced `write_file` illustration plus a real `read_file`, expecting only
  `read_file` to survive;
- malformed JSON and a string-valued `args`, expecting skip/error rather than
  an exception;
- two calls in one response, expecting ordered execution and two result
  blocks;
- a launch result with PID 4321 followed by prose claiming PID 99999,
  expecting 4321 in the worker result;
- a path `../escape.txt` and command `echo hello; touch injected.txt`,
  expecting a JSON error or literal echo and no write outside the workspace.
