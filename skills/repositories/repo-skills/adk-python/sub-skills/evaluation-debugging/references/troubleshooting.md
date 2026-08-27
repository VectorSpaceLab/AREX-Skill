# Troubleshooting

Use symptom-first diagnosis. Separate deterministic fixture/schema problems from environment-dependent model, credential, cloud, and server problems.

## Eval JSON Schema Mismatch

Symptoms:

- `ValueError: ... must contain a list of dictionaries.`
- `Exactly one of conversation and conversation_scenario must be provided in an EvalCase.`
- `Samples for tool_trajectory_avg_score must include 'query' and 'expected_tool_use' keys.`
- `Samples for response_match_score must include 'query' and 'reference' keys.`
- Pydantic validation errors for `Content`, `Part`, `FunctionCall`, `EvalCase`, or `EvalSet`.

Likely causes:

- Mixing `adk test` event fixture format with `adk eval` EvalSet format.
- New EvalSet object missing `eval_set_id`, `eval_cases`, `eval_id`, or `conversation`/`conversation_scenario`.
- Old-format list rows missing metric-required fields.
- GenAI `Content` uses the wrong casing or part shape.
- `functionCall`/`functionResponse` IDs are mismatched in replay fixtures.

Fixes:

1. Decide the intended path: `adk test` event replay or `adk eval` metric evaluation.
2. For `adk test`, use top-level `events` and optional `mocks`; include a first user text event.
3. For `adk eval`, use an EvalSet object with `eval_cases`, or use the old list format only when maintaining legacy data.
4. For static EvalSet cases, set `conversation` and leave `conversation_scenario` unset; for simulator cases do the reverse.
5. Keep `user_content` and `final_response` as GenAI-style content objects: `{"role": "user", "parts": [{"text": "..."}]}`.
6. For old-format data with default criteria, include both `expected_tool_use` and `reference` unless the config removes the corresponding metric.
7. Use `AgentEvaluator.migrate_eval_data_to_new_schema(old_file, new_file)` when an old fixture needs to become a current EvalSet.

## Missing Eval Dependencies

Symptoms:

- `Eval module is not installed, please install via pip install "google-adk[eval]".`
- Import errors for `pandas`, `tabulate`, evaluator internals, or Vertex evaluation utilities.

Likely causes:

- The base `google-adk` install does not include optional eval extras.
- Detailed result printing imports table-rendering dependencies.
- Scenario generation or judge-backed evaluation pulls optional dependencies.

Fixes:

1. Confirm the installed package and CLI surface with `python -c "import google.adk; print(google.adk.__file__)"` and `adk eval --help`.
2. Install the eval extra in the user's environment when they approve: `pip install "google-adk[eval]"`.
3. If only schema/static checks are needed, avoid judge/scenario-generation paths and run unit-level fixture validation instead.
4. If GCS eval storage is used, install GCP extras and set `GOOGLE_CLOUD_PROJECT`.

## Missing Model Credentials In Eval

Symptoms:

- Authentication failures during inference or judge-model evaluation.
- `GOOGLE_API_KEY`, Vertex credentials, project, region, or quota errors.
- Local deterministic tests pass, but `adk eval` fails while generating inferences or scores.

Likely causes:

- The evaluated agent model needs credentials.
- LLM-as-judge, rubrics, safety, hallucination, or scenario-generation metrics need a judge model.
- `InferenceConfig.parallelism` or `EvaluateConfig.parallelism` triggers quota limits.

Fixes:

1. Identify whether the failure happens during agent inference or during metric evaluation.
2. Run deterministic checks first: schema validation, `adk test`, or metrics that do not call an external judge.
3. Confirm the agent model and judge model names in `EvalConfig` and agent construction.
4. Ask the user to provide credentials through their normal environment; do not print or store credential values.
5. Lower parallelism and sample counts for quota-sensitive runs.
6. For CI, split credential-free replay/unit checks from credentialed eval jobs.

## Flaky LLM Assertions

Symptoms:

- Eval passes/fails intermittently.
- `response_match_score` fails on harmless wording changes.
- Tool trajectory score varies because the model sometimes calls extra tools or changes argument order.
- Rubric/judge scores vary across runs.

Likely causes:

- Assertions are too exact for stochastic model output.
- Tool trajectory uses `EXACT` when extra calls are acceptable.
- `num_runs`, judge `num_samples`, temperature, or model choice amplifies variance.
- The fixture relies on wall-clock time, random values, network state, or mutable session state.

Fixes:

1. Move deterministic logic into `adk test` fixtures with mocks when exact event flow matters.
2. Use `ToolTrajectoryCriterion.match_type` `IN_ORDER` or `ANY_ORDER` when order or extra calls are not the point.
3. Prefer targeted rubrics over broad final-text matching when multiple phrasings are acceptable.
4. Lower model randomness in the agent or judge config when supported.
5. Increase `num_runs` for confidence only after the assertion is well scoped.
6. Add stable `session_input.state` and explicit tool mocks for date/random/state-sensitive behavior.
7. Review detailed per-invocation output before changing thresholds.

## Tool Calls Not Observed

Symptoms:

- `expected_tool_use` is present but actual tool calls are empty.
- `tool_trajectory_avg_score` is `0`.
- `adk test` diff shows final text but no `functionCall` event.
- The web UI shows a response but no tool execution.

Likely causes:

- Tool is not bound to the running agent or sub-agent.
- The model did not receive a tool declaration because callbacks/plugins altered the request.
- Expected function name or args do not match the actual schema.
- The tool call happens in a child agent/node and the assertion filters the wrong author/path.
- Tool confirmation/HITL generated system function calls that were omitted from the fixture.
- A callback returned a response before the model/tool path ran.

Fixes:

1. Use verbose event printing or `scripts/summarize_adk_events.py` to list actual `functionCall` parts.
2. Inspect `nodeInfo.path`, not just `author`, for workflow/sub-agent routing.
3. Compare exact function names and argument keys; Pydantic/tool schema aliases can change the args shape.
4. Confirm callbacks: `before_model_callback`, `after_model_callback`, `before_tool_callback`, `after_tool_callback`, and `on_tool_error_callback`.
5. For EvalSet scoring, use `get_all_tool_calls()` semantics: calls come from `IntermediateData.tool_uses` or `InvocationEvents.invocation_events` content parts.
6. For replay fixtures, include matching `functionCall.id`/`functionResponse.id` and required system HITL events.
7. If the model simply chose not to call a tool, debug prompt/tool declaration in the agent-construction or tools-and-integrations sub-skill.

## Server Session Not Found

Symptoms:

- `404` or not-found errors for `/apps/{app}/users/{user}/sessions/{session}`.
- Session appears in the UI for one user/app but curl cannot fetch it.
- Eval-generated sessions are missing from list responses.

Likely causes:

- App name, user id, or session id mismatch.
- The server is using a different session service or local-storage location than the process that created the session.
- Eval sessions are intentionally filtered from normal session lists.
- The server restarted with in-memory sessions.
- `adk web` was started against a different agents directory.

Fixes:

1. Check `/health` and `/list-apps` on the same host/port.
2. List sessions with the exact app and user id before fetching one session.
3. Confirm whether the session was created through `/run`, `/run_sse`, web UI, or eval.
4. If using persistent services, confirm the same `session_service_uri` and local-storage behavior are active.
5. If the process restarted and used in-memory sessions, reproduce the session or switch to a persistent service with user approval.
6. Do not delete sessions while debugging; fetch and summarize instead.

## Trace Attributes Missing Or Disabled

Symptoms:

- `/dev/apps/{app}/debug/trace/session/{session}` returns no spans.
- Spans exist but `gcp.vertex.agent.llm_request` or `gcp.vertex.agent.llm_response` is `{}` or absent.
- Event IDs do not line up with expected trace spans.
- Trace is available only for newer sessions.

Likely causes:

- The server was not started with tracing exporters or local in-memory trace capture active for the relevant session.
- Content capture settings suppress prompt/response payloads.
- The session was created before tracing started or after spans were cleared.
- The route prefix is wrong; dev routes use `/dev/apps/{app}/debug/trace/...`.
- The model call failed before response attributes were recorded.

Fixes:

1. Confirm the route prefix and app name.
2. Fetch session events first; events are the source of truth when trace content is missing.
3. Look for span names and event IDs even if content payload attributes are empty.
4. Use verbose server logs and `print_event` output as fallback.
5. Reproduce with tracing enabled only if the user approves starting/restarting the server.
6. Redact or truncate `llm_request`, `llm_response`, tool args, and session state before sharing.

## `adk test` Fixture Diff Is Noisy

Symptoms:

- Diffs contain IDs, timestamps, model metadata, token usage, or empty action dictionaries.
- Parallel workflow events appear in unexpected order.
- RequestInput/HITL function IDs changed.

Likely causes:

- Fixture was hand-edited without the runner's normalization assumptions.
- Parallel nodes are being asserted as if they run in stable order.
- Stored IDs no longer match function response IDs.

Fixes:

1. Re-run focused replay first: `adk test AGENTS_DIR -- -k TEST_STEM -q`.
2. Use the summarizer to compare semantic fields: author, node path, text, calls, responses, output, actions.
3. Confirm function response IDs point to the remapped function call IDs.
4. If behavior intentionally changed, run `adk test AGENTS_DIR --rebuild` only for approved fixture updates.
5. For parallel output, assert key calls/responses rather than relying on incidental ordering when possible.

## `adk eval` Cannot Find The Agent Or Eval Set

Symptoms:

- Agent module path errors.
- `Module ... does not have a member named agent`.
- `root_agent` or `get_agent_async` not found.
- Eval set id not found.

Likely causes:

- `adk eval` expects an agent `__init__.py` path whose module contains an `agent` module/member with `root_agent`.
- App name is derived from the basename of the agent module file path.
- EvalSet IDs are resolved relative to the agent parent directory unless GCS storage is used.
- File path and EvalSet ID inputs were mixed.

Fixes:

1. Verify the file path points to the agent package `__init__.py`, not an arbitrary script.
2. Run a simple app-loading command or import check before eval.
3. Use EvalSet file paths for ad hoc local runs; use IDs only after creating/storing eval sets in the expected app directory.
4. Do not mix EvalSet file paths and IDs in the same `adk eval` call.
5. Route persistent app-discovery issues to `cli-configuration-deployment`.

## Safe Triage Order

1. Identify the workflow: `adk test`, `adk eval`, `AgentEvaluator`, web session, or trace.
2. Validate JSON shape and command help without credentials.
3. Summarize actual events with the bundled script.
4. Check exact tool names, args, node paths, and function response IDs.
5. Inspect detailed eval output or trace spans with truncation/redaction.
6. Escalate to credentialed model/cloud/server reproduction only when local deterministic checks cannot answer the question.
