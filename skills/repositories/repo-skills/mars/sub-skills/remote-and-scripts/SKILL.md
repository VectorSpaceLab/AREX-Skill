---
name: remote-and-scripts
description: "Routes Mars remote.spawn, ExecutableTuple, fetch_log, and
  script-run workflow requests to the verified remote-execution guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Remote Execution and Script Workflows

Use this sub-skill when the user wants Mars remote functions, nested DAGs,
returned logs, or a script-run style workflow. It is the right place for
`mars.remote.spawn`, `ExecutableTuple`, `fetch_log`, and the `run_script`
contract.

## Trigger phrases

- "Run these functions in parallel with Mars."
- "How do I use `mars.remote.spawn`?"
- "How do I fetch logs from a Mars task?"
- "How do I run a Python script on Mars workers?"
- "How do I pass one spawned result into another?"

## What belongs here

- `mars.remote.spawn` and nested dependency graphs.
- `mars.remote.ExecutableTuple` fan-in.
- `fetch_log` usage and log offsets.
- `run_script` and script-style workflow guidance.

## What stays elsewhere

- Tensor/DataFrame execution -> `tensor-dataframe-core`.
- Learner/integration APIs -> `learn-and-integrations`.
- Ray/GPU/Kubernetes/YARN or CLI help -> `deployment-and-backends`.

## Read these bundled files

- `references/api-reference.md` for the verified remote signatures.
- `references/workflows.md` for fan-out/fan-in and log retrieval patterns.
- `references/troubleshooting.md` for the common execution and log failures.
- `scripts/check_mars_remote.py` for a safe local smoke.

## Minimal route

1. Import `mars.remote as mr`.
2. Wrap a function with `mr.spawn(...)`.
3. Call `.execute().fetch()` when you need the result.
4. Use `mr.ExecutableTuple([...]).execute().fetch()` for explicit fan-in.
5. Use `fetch_log()` only when the session is distributed and logs are expected
   to come back to the client.

## Common decisions

- Keep the function body and its arguments tiny when demonstrating the API.
- Use nested spawn only when one remote function depends on another remote
  result.
- Treat `run_script` as a workflow contract, not as a reason to depend on the
  original repo's sample scripts.
- If the user asks for a quick check rather than a full cluster, prefer the
  bundled smoke helper and a local spawn example.

## Quality bar

A future agent should be able to explain how remote tasks are composed,
executed, and retrieved; how to fan out and fan in results; how logs are
retrieved; and when the script-run contract is appropriate.
