---
name: "disagg"
description: "Routes LightX2V disaggregated deployment workflows for the
  controller, encoder, transformer, and decoder services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Disaggregated deployment

Use this sub-skill for the multi-process LightX2V deployment stack that splits work across controller, encoder, transformer, and decoder roles.

## Typical triggers

- "run the disaggregated LightX2V stack"
- "launch controller / encoder / transformer / decoder"
- "debug Mooncake, RDMA, or ZMQ setup"
- "single-node versus multi-node disaggregation"
- "understand `run_dynamic.sh` or `run_baseline.sh`"

## Read first

- [`references/workflows.md`](references/workflows.md) for the launch patterns and the role-by-role command flow.
- [`references/topology.md`](references/topology.md) for the service roles, ports, and config fields that control placement.
- [`references/troubleshooting.md`](references/troubleshooting.md) for port, backend, and world-size failures.
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for cross-cutting import and dependency failures.

## What belongs here

Include:
- `python -m lightx2v.disagg.examples.run_service`
- `python -m lightx2v.disagg.examples.run_controller`
- `python -m lightx2v.disagg.examples.run_user`
- controller / encoder / transformer / decoder role planning
- dynamic and baseline disagg launch patterns
- Mooncake / RDMA / ZMQ transport notes
- single-node and multi-node deployment guidance
- request routing, stage metrics, and service topology

Exclude or route elsewhere:
- direct local generation → `sub-skills/inference/`
- HTTP server and queue management → `sub-skills/serving/`
- checkpoint surgery or conversion → `sub-skills/conversion/`

## Safe starting checks

- `python scripts/check_install.py`
- `python sub-skills/disagg/scripts/plan_launch.py --config_json /path/to/config.json`
- `python -m lightx2v.disagg.examples.run_service --help`
- `python -m lightx2v.disagg.examples.run_controller --help`
- `python -m lightx2v.disagg.examples.run_user --help`

## Guidance style

For disaggregated deployment questions, always identify:
- the service role
- the topology (`single_node` or `multi_node`)
- the config file that determines the role map
- the ports or addresses that the role must bind
- whether the workflow uses the package entry point directly or a shell launcher

## Decision points

When helping with disaggregated deployment, resolve these questions first:
- topology: `single_node` or `multi_node`
- scope: controller-only planning, individual worker startup, or a full role set
- config source: the disagg JSON that declares the role map and transport settings
- transport: whether the run depends on ZMQ, RDMA, Mooncake, or a simpler local path
- execution mode: a shell launcher, a package entry point, or a safe command plan only

Common reminders:
- the controller, encoder, transformer, and decoder all have distinct responsibilities
- the rank and port plan must match the config file and the number of visible GPUs
- the planner helper is the safe way to inspect a deployment before starting processes
- `run_dynamic.sh` and `run_baseline.sh` are documented mainly as launch patterns, not as direct bundled runtime code
- if transport or bind failures appear, check stale processes and port collisions before changing the model config

## What a good answer should contain

For a future agent, a strong answer from this route should usually include:
- the topology and the service role(s)
- the config file that defines the role map
- the ports, addresses, or bootstrap values that matter
- the launch order and whether a shell wrapper or package entry point is better
- any transport note about ZMQ, RDMA, or Mooncake prerequisites

If the user only wants the command plan, use the bundled planner helper. If they want the actual deployment sequence, read the workflow reference and then answer with the exact role-by-role launch order.
