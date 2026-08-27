---
name: workflow-orchestration
description: "Build and debug ADK 2.0 Workflow graphs, BaseNode/function nodes,
  graph routing, dynamic nodes, HITL, retry, checkpoint/resume, and workflow
  event flow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ADK Workflow Orchestration

Use this sub-skill when the task is to build or debug ADK 2.0 `Workflow` graphs, custom `BaseNode`/`FunctionNode` steps, static and dynamic graph routing, joins, parallel workers, retries, human-in-the-loop interruptions, workflow event paths, or resume/checkpoint behavior.

## Route requests

- **Create a graph**: Use [Workflow patterns](references/workflow-patterns.md) for `Workflow(edges=...)`, `START`, chain tuples, explicit `Edge`, route maps, `JoinNode`, parallel worker, dynamic fan-out/fan-in, state, and output patterns.
- **Check APIs**: Use [API reference](references/api-reference.md) for constructor signatures, node fields, `Context.run_node`, `Event`, `NodeInfo`, `RequestInput`, and `RetryConfig` names.
- **Debug execution**: Use [Troubleshooting](references/troubleshooting.md) for deadlocks, runner vs node-runner confusion, rerun/resume surprises, dynamic node dedup, join stalls, route misses, timeouts, and retry expectations.
- **Inspect installed package**: Run [inspect_workflow_api.py](scripts/inspect_workflow_api.py) to print the local `google.adk.workflow` signatures and construct a tiny no-LLM function-node workflow object.

## Boundaries

- Use this sub-skill for `Workflow`, `BaseNode`, `node`, `FunctionNode`, `JoinNode`, `RetryConfig`, `RequestInput`, `Event`, `NodeInfo`, graph edges, dynamic nodes through `ctx.run_node`, checkpoint/resume semantics, and workflow state/output routing.
- Route LLM `Agent`/`LlmAgent` construction, model configuration, instructions, tools, callbacks, and schemas to `agent-construction`.
- Route `Runner`, `App`, session service, memory, artifacts, plugins, and persistence lifecycle details to `runtime-services`.
- Route repository maintainer test policy and source-code change validation to `repo-development`.

## Safe assumptions

- The installed distribution is `google-adk` 2.3.0 with import root `google.adk` and Python 3.10+.
- Base install may omit optional extras; workflow construction with pure function nodes does not require cloud credentials, network access, or LLM calls.
- `adk` CLI includes `api_server`, `conformance`, `create`, `deploy`, `eval`, `eval_set`, `migrate`, `optimize`, `run`, `test`, and `web`, but CLI/server/deploy usage belongs in the CLI sub-skill.
- Future guidance should not depend on source checkout files; copy or recreate needed snippets inside the agent’s working files.

## Quick validation

```bash
python scripts/inspect_workflow_api.py --help
python scripts/inspect_workflow_api.py
```

The script performs only local imports and object construction; it does not start a runner, call an LLM, access credentials, open a network connection, or write files.
