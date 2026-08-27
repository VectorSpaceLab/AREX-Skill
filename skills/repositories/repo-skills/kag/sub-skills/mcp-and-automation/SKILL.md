---
name: mcp-and-automation
description: "Routes KAG MCP server, cluster submission, and benchmark
  automation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MCP and Automation

Use this sub-skill when the user wants KAG to run as a service, a tool protocol endpoint, or a benchmark/cluster automation target.

## Triggers

Common requests include:

- start or validate `kag mcp-server`
- choose between `stdio` and `sse` transport
- validate MCP tool configuration before launch
- submit a distributed builder job with `kag builder`
- plan a benchmark run with `kag benchmark` or the open benchmark shell workflow
- inspect long-running service or automation side effects before executing them

## Start here

1. Read `references/mcp-workflows.md` for the server and tool surface.
2. Read `references/automation-and-benchmarks.md` for builder submission and benchmark planning.
3. Run `scripts/check_mcp_config.py` before a live MCP launch.
4. Run `scripts/plan_benchmark_command.py` before a benchmark or open-benchmark run.
5. Read `references/troubleshooting.md` when a port, tool name, API key, or benchmark mutation looks risky.

## What belongs here

This sub-skill owns the task families that launch or automate KAG from the outside:

- `kag mcp-server`
- MCP executor/tool config checks
- distributed builder submission
- benchmark command planning and dry-run helpers
- service-side config validation for long-running operations

## What does not belong here

- Project/schema setup and builder-chain choice go to `knowledge-construction`.
- Query-time reasoning and answer tracing go to `question-answering`.
- Generic install/import problems go to the root troubleshooting files.

## Common decisions

- Prefer `stdio` when the user wants an agent-friendly local launch.
- Use `sse` only when the user explicitly wants a networked server on a port.
- Check `qa-pipeline` and `kb-retrieve` separately because they have different config needs.
- Validate the builder submission with `--validity_check` before any remote job request.
- Treat benchmark planning as a dry-run first, especially when the workflow rewrites config files.
- If the user only wants a preview, return the dry-run plan instead of a live launch command.
- Do not confuse server readiness with tool readiness; validate both separately.
- Keep remote job submission and local service launch as separate approval steps.

## What a good answer should include

- the transport, port, and tool set for the MCP launch plan
- the config sections needed for the chosen tool or job
- whether the action is safe to preview or will mutate state
- the next command to run only after config validation passes
- any external service, API key, or cluster approval that is still missing

## Stop conditions

Stop and ask for confirmation when the task would:

- open a port or start a long-running server unexpectedly
- submit a remote builder job without a validity check
- patch benchmark config files or launch a live benchmark without approval
- depend on an external API key or service that has not been provided
- require background execution that the user has not explicitly allowed

## Bundled helpers

- `scripts/check_mcp_config.py` — static MCP launch/config validation.
- `scripts/plan_benchmark_command.py` — dry-run planning for benchmark and open-benchmark commands.
