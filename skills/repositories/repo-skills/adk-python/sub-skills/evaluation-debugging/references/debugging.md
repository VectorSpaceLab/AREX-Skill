# Debugging

Use this reference to inspect ADK behavior without immediately changing agent code. Start with a deterministic local run or existing session JSON, then escalate to web/API trace inspection only when needed.

## Debugging Modes

| Mode | Best for | Safe first check |
| --- | --- | --- |
| `adk run` | Fast CLI smoke tests, single queries, JSONL output, exit codes | `adk run --help` |
| `adk test` | Exact event replay for stored fixtures | `adk test AGENTS_DIR -- -k TEST -q` |
| `adk web` | Browser UI, sessions, trace inspection, eval-set editing | Check `/health` before starting a server |
| `adk api_server` | REST/SSE automation without UI | Use existing server/session if available |
| Programmatic `Runner` | Controlled unit tests and in-memory sessions | Use `InMemorySessionService` and explicit `types.Content` |

Do not start a server by default. If a user asks for server debugging, first ask whether one is already running or check its health endpoint if the base URL is known.

## `adk run` Local Debugging

Useful command shapes:

```bash
adk run path/to/agent_dir "What can you do?"
adk run --jsonl path/to/agent_dir "Roll a 6-sided die"
adk run -v path/to/agent_dir "Why did the tool not run?"
```

Debug checklist:

- Use query mode rather than interactive mode when automating.
- Use `--jsonl` when you need machine-readable events and less console noise.
- Use `-v` for debug logs when agent loading, callbacks, or tool execution is unclear.
- If state matters across turns, provide or preserve a session ID; otherwise use in-memory/isolated runs for reproducibility.
- Exit code `0` means success, `1` means error, and `2` can indicate paused/HITL workflow state.

## Event Model Fields To Inspect

ADK `Event` records can contain:

- `author`: the agent, workflow, or user that authored the event.
- `content.role`: usually `user` or `model`.
- `content.parts[].text`: natural-language output.
- `content.parts[].functionCall`: tool request with `id`, `name`, and `args`.
- `content.parts[].functionResponse`: tool result with `id`, `name`, and `response`.
- `output`: workflow/node output for graph-style execution.
- `actions.stateDelta`: session state mutations.
- `actions.transferToAgent`, `actions.requestTask`, `actions.finishTask`: transfer/task actions.
- `nodeInfo.path`: workflow graph/node path; this is often more precise than `author` for ADK 2.x workflows.
- `branch`: branch or invocation route information when present.
- `invocationId` and `id`: correlation fields, volatile in replay unless normalized.

For workflow events, `author` may be the enclosing workflow; filter by `nodeInfo.path` when isolating a specific node.

## Built-in Event Printing

ADK exposes `google.adk.utils._debug_output.print_event` for readable console output.

```python
from google.adk.utils._debug_output import print_event

print_event(event, verbose=False)  # Text responses only.
print_event(event, verbose=True)   # Tool calls, tool responses, code execution, inline data, files.
```

`print_event` truncates tool args, tool responses, and code output for readability. Use `verbose=True` when debugging a missing tool call or function response; use `verbose=False` for user-facing transcript checks.

## Programmatic In-memory Session Inspection

Use the published import root and explicit content objects:

```python
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

agent = Agent(name="debug_agent", model="gemini-2.5-flash", instruction="...")
runner = Runner(
    app_name="debug_app",
    agent=agent,
    session_service=InMemorySessionService(),
)
session = runner.session_service.create_session_sync(app_name="debug_app", user_id="u1")
message = types.Content(role="user", parts=[types.Part.from_text(text="hello")])
for event in runner.run(user_id="u1", session_id=session.id, new_message=message):
    print_event(event, verbose=True)
```

Important API facts:

- `Runner.run` requires keyword arguments `user_id`, `session_id`, and `new_message`; `state_delta` and `run_config` are optional.
- Use `types.Content` for portable tests; plain strings may work in helpers but are less explicit.
- Read session state after the run through the session service when verifying persisted `actions.stateDelta`.
- Keep tool and model credentials outside logs and fixture files.

## Web/API Server Session Inspection

When a server is already running, inspect without mutating first:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/list-apps | python -m json.tool
curl -s http://127.0.0.1:8000/apps/APP/users/USER/sessions | python -m json.tool
curl -s http://127.0.0.1:8000/apps/APP/users/USER/sessions/SESSION | python -m json.tool
```

Create and run only when needed:

```bash
SESSION=$(curl -s -X POST http://127.0.0.1:8000/apps/APP/users/debug-user/sessions \
  -H "Content-Type: application/json" \
  -d '{}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')

curl -N -X POST http://127.0.0.1:8000/run_sse \
  -H "Content-Type: application/json" \
  -d "{\"app_name\":\"APP\",\"user_id\":\"debug-user\",\"session_id\":\"$SESSION\",\"new_message\":{\"role\":\"user\",\"parts\":[{\"text\":\"hello\"}]},\"streaming\":false}"
```

Do not delete sessions after debugging unless the user explicitly asks; the UI may still need them.

## Dev Trace Endpoints

The ADK web/dev server exposes trace routes under the dev app prefix:

```bash
curl -s http://127.0.0.1:8000/dev/apps/APP/debug/trace/EVENT_ID | python -m json.tool
curl -s http://127.0.0.1:8000/dev/apps/APP/debug/trace/session/SESSION | python -m json.tool
```

Trace span records can include:

- `name`: common values include `call_llm`, `send_data`, and `execute_tool...`.
- `attributes.gcp.vertex.agent.event_id`: event correlation.
- `attributes.gcp.vertex.agent.llm_request`: serialized LLM request when content capture is enabled.
- `attributes.gcp.vertex.agent.llm_response`: serialized LLM response when content capture is enabled.
- `attributes.gen_ai.request.model`: model name.
- `attributes.gen_ai.usage.input_tokens` and `attributes.gen_ai.usage.output_tokens`: token counts when available.
- `attributes.gen_ai.response.finish_reasons`: finish reasons when available.
- `span_id`, `trace_id`, and `parent_span_id`: trace tree correlation.

Content capture can be disabled or partially routed depending on telemetry settings. Missing `llm_request` or `llm_response` does not necessarily mean no model call happened; correlate with session events and span names.

## Summarizing Sessions And Events

Use the bundled summarizer for raw JSON from sessions, `adk run --jsonl` captures, event replay fixtures, or trace-like dumps:

```bash
python sub-skills/evaluation-debugging/scripts/summarize_adk_events.py --input session.json
curl -s http://127.0.0.1:8000/apps/APP/users/USER/sessions/SESSION \
  | python sub-skills/evaluation-debugging/scripts/summarize_adk_events.py --max-text 160
```

The script prints author, branch/node path, text, function calls/responses, output, and actions while truncating long values.

## Isolating Missing Tool Calls

When an expected tool call is not observed:

1. Confirm the tool is actually declared on the agent or available through its toolset for the current run.
2. Confirm the model received the tool declaration by inspecting verbose event output or a `call_llm` trace request when content capture is available.
3. Compare expected function name exactly; eval/test assertions do not forgive renamed tools.
4. Compare argument shape exactly for `EXACT` tool trajectory checks; use `IN_ORDER` or `ANY_ORDER` only when extra calls are acceptable.
5. Check callbacks: `before_tool_callback`, `after_tool_callback`, `on_tool_error_callback`, model callbacks, and plugins can alter calls, responses, or final output.
6. For HITL/confirmation flows, include the system function calls and matching user `functionResponse` events in replay fixtures.
7. For workflow graphs, inspect `nodeInfo.path`; the correct tool may run in a child node while the enclosing `author` stays constant.

## Isolating Callback Ordering

For a user request like “summarize a failed `adk web` session trace and isolate model/tool callback ordering without exposing secrets”:

1. Fetch the session JSON and run the bundled summarizer with a small `--max-text`.
2. Fetch the session trace and identify `invoke_agent`/node spans, `call_llm`, `execute_tool`, and `send_data` order by parent/child span and start/end times if present.
3. Correlate `gcp.vertex.agent.event_id` with summarized events.
4. Inspect only redacted/truncated `llm_request`, `llm_response`, tool args, and tool responses.
5. Check whether callback-generated events or plugin side effects appear before or after the model/tool spans.
6. If trace content is missing, rely on event order plus verbose server logs; do not assume content capture was enabled.

## Debug Logs

Useful server flags:

```bash
adk web -v path/to/agents_dir
adk web --reload_agents path/to/agents_dir
adk api_server --log_level DEBUG path/to/agents_dir
```

Safe logging rules:

- Prefer redirecting logs to a user-approved workspace file when an agent needs to inspect them.
- Do not paste full logs containing API keys, OAuth tokens, session state, tool args, or LLM prompts.
- Share focused excerpts with event IDs, span names, tool names, exception types, and redacted args.

## Native Debug Verification

For local, focused checks in this area:

```bash
adk test --help
adk eval --help
# In an ADK source checkout, run focused evaluation tests for eval-case models,
# eval config parsing, and local eval-set manager behavior.
```

Escalate to web/API server or model-backed evals only when the user needs runtime behavior that cannot be reproduced through in-memory runner, event replay, or unit-level evaluation tests.
