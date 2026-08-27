# Testing, VCR, and Nx

## Selection rule

Start with the smallest deterministic test that covers the change.
Move upward only if the lower layer does not exercise the modified surface.

## Minimal command shapes

- One package: `npx nx run <package>:test`
- Changed packages: `npx nx affected -t test`
- One file or node: `uv run pytest tests/<path>::<node> -q`
- Replay-only provider test: add `--record-mode=none`
- Refreshing cassettes: use an explicit record mode and valid credentials

## VCR record modes

| Mode | Meaning | Use it when |
| --- | --- | --- |
| `none` | Replay existing cassettes only | You want no re-recording and no credential use. |
| `once` | Replay if present, record if missing | You are adding a new episode and understand the side effects. |
| `new_episodes` | Append missing interactions | You need to extend a cassette without rewriting known traffic. |
| `all` | Re-record everything | You deliberately changed the API interaction and have approved credentials. |

## Cassette safety

- Never commit API keys or other secrets.
- Prefer environment variables or a secure vault for credentials.
- Scrub headers and payload fields before recording whenever the test framework allows it.
- Treat stale or missing cassettes as a signal to switch to a safer test, not as a reason to invent traffic.
- If a test needs live credentials, keep that fact explicit in the test selection notes.

## Safe native verification categories

| Category | Why it is safe | Good first check |
| --- | --- | --- |
| Semantic-convention tests | No network, no cassette refresh, no provider credentials | `opentelemetry-semantic-conventions-ai` attribute and compliance tests |
| SDK offline tests | Use in-memory or console exporters and local span processors | `traceloop-sdk` initialization, decorator, and workflow tests |
| Replay-only VCR tests | Existing cassettes can validate provider behavior without hitting live services | Small provider tests with `--record-mode=none` |
| Local-client tests | Exercise local or in-process clients without cloud accounts | MCP or local vector-client tests when their dependency is installed |
| Credentialed live tests | Validate true API behavior | Only when the change truly needs traffic refresh |

## Representative native candidates

These are useful verification candidates when the change touches the corresponding surface:

- `packages/opentelemetry-semantic-conventions-ai/tests/test_span_attributes.py`
- `packages/opentelemetry-semantic-conventions-ai/tests/test_semconv_compliance.py`
- `packages/traceloop-sdk/tests/test_sdk_initialization.py::test_get_default_span_processor`
- `packages/traceloop-sdk/tests/test_sdk_initialization.py::test_multiple_span_processors`
- `packages/traceloop-sdk/tests/test_agent_workflow_context.py`
- `packages/traceloop-sdk/tests/test_tasks.py`
- Small provider semconv or behavior tests that already ship with cassettes
- Local-client tests for MCP, Chroma, Qdrant, Milvus, or LanceDB when the optional dependency is present

## Minimal instrumentation-change path

For a package-level instrumentation change that should not re-record cassettes:

1. Pick the smallest no-network test in that package.
2. If the test is cassette-backed and the cassette already exists, run it with `--record-mode=none`.
3. If no cassette-backed no-network test exists, fall back to a semconv or import-only check first.
4. Only move to `once`, `new_episodes`, or `all` when the behavior change truly needs refreshed traffic.

## Nx use in verification

Use Nx when the change spans more than one package or when you need workspace-wide dependency awareness.
Use direct `uv run pytest ...` when a single file or node is the smallest meaningful check.

## Do not overclaim

- A skipped live-service test is not a pass.
- A CPU import is not evidence for a live service or external backend.
- Do not refresh cassettes unless the change actually affects the recorded traffic.
