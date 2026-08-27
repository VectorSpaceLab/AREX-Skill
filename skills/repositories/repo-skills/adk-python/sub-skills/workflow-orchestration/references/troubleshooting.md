# Workflow Orchestration Troubleshooting

Use this guide when an ADK 2.0 workflow stalls, reruns unexpectedly, fails graph validation, loses state/output, or mishandles HITL resume. All checks are local reasoning steps unless a user explicitly asks to execute an app.

## Quick triage

1. Identify whether the problem is graph construction, scheduling, node execution, event/output routing, or runner/session resume.
2. Confirm the root object is a `Workflow` for graph orchestration, not a legacy sequential agent pattern.
3. Print local signatures with `scripts/inspect_workflow_api.py` if the installed package may differ.
4. Inspect emitted events for `node_info.path`, `output`, `actions.state_delta`, `actions.route`, `long_running_tool_ids`, and `node_info.output_for`.
5. Route session persistence, `Runner`, database services, and app loading issues to `runtime-services` or CLI guidance.

## Graph validation failures

### Duplicate node names

Symptom:

- Construction fails with duplicate names.

Cause:

- Two distinct callable/node objects compile to the same node name, often from repeated function names or copied `FunctionNode(name=...)` values.

Fix:

- Give every distinct node a unique Python-identifier name with `@node(name="...")` or `FunctionNode(..., name="...")`.
- Reuse the exact same node object only when the graph intentionally loops back to that node.

### Missing or invalid START

Symptom:

- Construction says `START` is missing or has incoming edges.

Fix:

- Include exactly an entry edge from `START` or `"START"` to the first node.
- Do not route any edge into `START`.

### Unreachable nodes

Symptom:

- Construction lists unreachable nodes.

Fix:

- Connect every node to a path reachable from `START`.
- Remove unused nodes from `edges`.

### Duplicate edges

Symptom:

- Construction rejects a repeated `from_node -> to_node` edge.

Fix:

- Combine route values into one edge route list where appropriate, except `DEFAULT_ROUTE` must be its own edge.
- Remove accidental duplicate chain/explicit edge declarations.

### Unconditional cycle

Symptom:

- Construction rejects `A -> B -> A` or similar.

Fix:

- Make at least one loop edge conditional by yielding `Event(route="continue")`, and add an exit route.

### Schema mismatch

Symptom:

- Construction rejects an edge because `output_schema` and `input_schema` differ.

Fix:

- Align adjacent node schemas exactly.
- Add a transform node between incompatible schemas.
- For raw dict JSON-schema surfaces, remember descriptive schemas may not coerce values the same way Pydantic model classes do.

### Chat or task agent wiring errors

Symptom:

- A static graph node using an agent mode fails validation.

Fix:

- Chat-mode agents should only follow `START` in a workflow graph.
- Task-mode agents cannot be static graph nodes; use them as sub-agents under an agent coordinator or dispatch dynamically from a custom node.
- Route detailed `Agent` construction and mode selection to `agent-construction`.

## Deadlocks and stalls

### Runner vs NodeRunner confusion

Symptom:

- A developer tries to start a `Runner` from inside a node, or a workflow waits forever while nested execution is manually managed.

Cause:

- Public `Runner` owns application invocation/session lifecycle. Workflow child execution is owned by internal `NodeRunner` and `Context.run_node()`.

Fix:

- Inside a workflow node, call `await ctx.run_node(child, node_input=...)` rather than creating a public `Runner`.
- Do not start separate session/app runners from inside node logic unless you are intentionally leaving workflow orchestration.

### `wait_for_output=True` waits forever

Symptom:

- Node enters `WAITING` and no downstream node runs.

Cause:

- The node completed without output or route while `wait_for_output=True`.

Fix:

- Ensure a later trigger will re-enter that node and eventually emit output/route.
- If it is not a barrier/accumulator, remove `wait_for_output=True`.
- If it should propagate a wait from a child dynamic node, call `ctx.run_node(..., raise_on_wait=True)`.

### JoinNode never runs

Symptom:

- Static branches complete partly, but `JoinNode` never emits aggregate output.

Cause:

- `JoinNode` waits for every predecessor declared by incoming graph edges. A conditional predecessor that is not taken still counts as an expected predecessor if wired into the join.

Fix:

- Only wire unconditional fan-out branches into one `JoinNode`.
- For conditional paths, put a join inside each route path or normalize routes to a common predecessor that always executes.
- Verify every predecessor produces output if the downstream aggregator expects non-`None` values.

### Dynamic fan-out appears hung

Symptom:

- Parent orchestrator never finishes after launching dynamic children.

Fix:

- Ensure all `ctx.run_node()` calls are awaited directly or through `asyncio.gather`.
- Do not create unsupervised `asyncio.create_task(ctx.run_node(...))` tasks.
- Use `use_sub_branch=True` for parallel dynamic children.
- Check child nodes for unresolved `RequestInput` interrupts or long-running tool IDs.

## Resume and HITL surprises

### Parent node errors: `rerun_on_resume=True` required

Symptom:

- Runtime error says a node must have `rerun_on_resume=True` because it dynamically scheduled nodes.

Fix:

- Decorate the parent with `@node(rerun_on_resume=True)` or construct `FunctionNode(..., rerun_on_resume=True)`.
- Apply the same rule to any dynamic child that itself calls `ctx.run_node()`.

### Node reruns on resume

Symptom:

- Code before a HITL prompt or dynamic child executes again after the user responds.

Cause:

- Nodes with `rerun_on_resume=True` re-execute to reconstruct control flow and collect child results.

Fix:

- Keep parent orchestration code side-effect-light.
- Move irreversible side effects into child nodes with deterministic paths; completed child outputs are deduplicated from session events.
- Read `ctx.resume_inputs` at the top of HITL nodes and branch deterministically.

### Node skips on resume

Symptom:

- A child node does not run again after resume.

Cause:

- Completed static nodes may be intercepted from recovered session events.
- Completed dynamic nodes are deduplicated by full `node_path` and return cached output.

Fix:

- Inspect `Event.node_info.path` and run IDs to confirm the node previously completed.
- If re-execution is desired, use a different deterministic node path/run ID and ensure semantics tolerate repeated work.
- Do not use random names or time-based run IDs; they break predictable recovery.

### Partial HITL responses behave differently across nodes

Symptom:

- One waiting node resumes with a partial response while another remains waiting, or a leaf completes without re-running.

Cause:

- `rerun_on_resume=True` orchestration nodes re-execute with partial `resume_inputs`.
- `rerun_on_resume=False` leaf nodes wait for all interrupts or complete from resolved responses without running custom code.

Fix:

- For custom HITL logic that must inspect partial or full responses, set `rerun_on_resume=True`.
- Use stable `interrupt_id` values and read `ctx.resume_inputs[interrupt_id]`.
- Make route decisions explicit with `Event(route=...)` or `ctx.route`.

### RequestInput response not delivered

Symptom:

- A node repeatedly asks for the same input after the user responded.

Fix:

- Match the resume function response ID to `RequestInput.interrupt_id`.
- Match the function name used by the request-input protocol (`adk_request_input`) in clients that manually construct responses.
- Confirm session events belong to the same invocation/session; runner/session issues route to `runtime-services`.

## Dynamic node dedup and branch isolation

### Dynamic child reruns unexpectedly

Cause:

- Its full path changed: parent path, child node name, auto-generated child run counter, or explicit run ID differs from the first run.

Fix:

- Use stable child node names and stable explicit run IDs for data-dependent fan-out, such as `run_id=f"item_{index}"`.
- Do not use random, timestamp, or content-hash values that can change across resume unless the changed path is intentional.
- Explicit run IDs must contain non-numeric text to avoid collision with auto IDs.

### Dynamic child output appears under wrong branch

Cause:

- Parallel children ran without sub-branch isolation.

Fix:

- Pass `use_sub_branch=True` for each parallel `ctx.run_node()` call.
- Inspect `event.branch` and `event.node_info.path` to ensure sibling runs are separated.

### Parent output duplicates child output

Cause:

- Parent uses `use_as_output=True` and also yields its own output.

Fix:

- Choose one output path: either delegate with `use_as_output=True` or yield `Event(output=...)` from the parent.
- Inspect `Event.node_info.output_for` to confirm delegated ancestor outputs.

## Output, route, and state problems

### UI shows nothing, but workflow returned data

Cause:

- `Event(output=...)` is internal workflow data, not necessarily visible UI content.

Fix:

- Yield `Event(message="...")` for user-visible text.
- Yield a separate `Event(output=...)` when downstream nodes need structured data.

### Downstream receives `None`

Cause:

- The predecessor emitted only a message, route, or state delta without output.

Fix:

- Return/yield a raw value or `Event(output=value)` when downstream nodes need data.
- If the data is in state, make downstream nodes read named state parameters or `ctx.state`.

### Route edge not taken

Cause:

- The node did not emit a route value, emitted a mismatched value, or used a list that did not intersect edge route values.

Fix:

- Yield `Event(route="expected")` or set `ctx.route = "expected"`.
- Add `DEFAULT_ROUTE` for fallback.
- Remember route values are `str`, `int`, or `bool`.

### State parameter missing

Symptom:

- A `FunctionNode` says a required parameter was not found in state.

Cause:

- Default `parameter_binding="state"` binds non-context, non-`node_input` parameters from `ctx.state`.

Fix:

- Rename the parameter to `node_input` if it should receive predecessor output.
- Use `@node(parameter_binding="node_input")` and pass a dict if you want dict-key binding from dynamic input.
- Set or validate the expected state key before the node runs.

### State schema rejects function parameters

Cause:

- Workflow has `state_schema`, and a state-bound `FunctionNode` declares a non-context parameter not present in the schema.

Fix:

- Add the key to the Pydantic state schema.
- Rename the parameter to `node_input` if it is not a state key.
- Use `parameter_binding="node_input"` for dict inputs.

## Retry, timeout, and failure expectations

### Retry did not happen

Possible causes:

- `max_attempts` is `0` or `1`.
- Raised exception class/name is not listed in `RetryConfig.exceptions`.
- The failure occurred outside the node execution path.

Fix:

- Use `RetryConfig(max_attempts=3, exceptions=None)` to retry all exceptions while testing.
- Set `jitter=0.0` for deterministic validation.
- Confirm the retry config is attached to the node that actually raises.

### Timeout did not stop a child operation

Cause:

- Timeout applies to the node execution as observed by the node runner. Blocking synchronous code may delay cancellation.

Fix:

- Prefer async I/O inside async nodes.
- Put blocking work behind safe timeouts at the library/client layer as well.
- Attach `timeout` to the node that owns the slow operation.

### Retry duplicated side effects

Cause:

- Retried node performed non-idempotent work before raising.

Fix:

- Add idempotency keys or dedupe checks.
- Split side effects into a small child node after validation/approval.
- Avoid retrying irreversible operations unless the operation itself is idempotent.

### Retry attempts reset after resume

Cause:

- Retry attempt count is in-memory and not persisted across HITL/resume or process restart.

Fix:

- Store business-level attempt counters in state if they must survive resume.
- Do not rely on `RetryConfig` as durable workflow policy.

## Optional extras, credentials, and data assumptions

- Pure workflow graph construction, function nodes, joins, events, retries, and `RequestInput` do not require cloud credentials or network access.
- LLM agent nodes require model/provider configuration and credentials; route construction details to `agent-construction`.
- Persistent sessions, databases, memory, artifacts, and cloud services can require optional extras; route those setup issues to `runtime-services`.
- The base install can omit optional extras such as database, extensions, MCP, and cloud integrations; missing optional imports are environment facts, not workflow graph blockers.

## Safe local validation commands

Use the bundled inspector first:

```bash
python scripts/inspect_workflow_api.py --help
python scripts/inspect_workflow_api.py
```

For a user’s own workflow module, safe validation can include:

- Importing the module without running a server or LLM call.
- Constructing the `Workflow` object to trigger graph validation.
- Checking that pure function nodes and `JoinNode` shapes produce expected local objects.
- Avoiding `Runner.run`, live model nodes, network tools, and credential-requiring integrations unless the user explicitly authorizes execution.
