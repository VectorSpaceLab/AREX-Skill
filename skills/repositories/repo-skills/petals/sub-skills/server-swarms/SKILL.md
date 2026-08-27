---
name: server-swarms
description: "Operate Petals server and DHT swarm commands for public capacity,
  private swarm testing, deployment choices, and workflow-specific
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Petals Server Swarms

Use this sub-skill to construct, review, or troubleshoot Petals server and DHT commands: public capacity contribution, local/private swarm bootstrap, block selection, device/dtype/cache/network options, Docker-style operation, reachability, quantization, or server-side adapters.

## First steps

1. Identify public versus private swarm operation.
2. Read [references/server-cli-reference.md](references/server-cli-reference.md) for exact flags and conflicts.
3. Read [references/private-swarms.md](references/private-swarms.md) for bootstrap and local CPU smoke patterns.
4. Read [references/operations.md](references/operations.md) for cache, Docker-style deployment, restart safety, and backend notes.
5. Prefer print-only builders:
   - `python scripts/build_server_command.py --help`
   - `python scripts/build_private_swarm_commands.py --help`
6. For failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries

Route client generation to `client-inference`, prompt-training semantics to `prompt-tuning`, tensor-parallel internals to `distributed-blocks`, and benchmark selection to `benchmarks-maintenance`.

## Safety rules

Petals DHT and server CLIs are long-running network services. Do not run them unless the user approved network/model/cache side effects. The bundled scripts print command plans only. Do not reuse one identity file across distinct peers. Treat quantization and adapter loading as optional backend features until verified.
