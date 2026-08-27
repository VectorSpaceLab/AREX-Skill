---
name: moe
description: "Routes Hivemind remote expert and mixture-of-experts workflows,
  including server setup, custom expert registration, and client-side expert
  routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Mixture of Experts

Use this route when the task is about `hivemind.moe.Server`, `ModuleBackend`, `RemoteExpert`, `RemoteMixtureOfExperts`, `RemoteSwitchMixtureOfExperts`, custom expert registration, or the `hivemind-server` command.

## Include

- Hosting experts with `hivemind.moe.server.Server` or `background_server`.
- Remote expert clients with `RemoteExpert` and the MoE routing layers.
- Declaring and discovering experts with `declare_experts` and `get_experts`.
- Custom expert classes via `register_expert_class` and `custom_module_path`.
- Checkpointing and backend scheduling behavior in `ModuleBackend`.
- The `hivemind-server` console command.

## Exclude

- DHT bootstrap and network reachability debugging; route that to `dht`.
- Optimizer wrapping, tensor averaging, and ALBERT training; route those to `collaborative-training`.
- Benchmarks and throughput experiments.

## Start here

1. Read [`references/api-reference.md`](references/api-reference.md) for the verified server/client signatures.
2. Read [`references/workflows.md`](references/workflows.md) for the standard server, client, and custom-expert flows.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when the server cannot publish experts, clients cannot find experts, or a custom module fails to load.
4. Run [`../../scripts/check_install.py`](../../scripts/check_install.py) from the generated skill tree to confirm the installed package and CLI entry points.

## What to remember

- `hivemind-server` is the package command for serving experts.
- `background_server(...)` is the fastest way to spin up a temporary expert host in tests or small demos.
- `client_mode` matters when a client can dial out but should not accept inbound connections.
- `custom_module_path` lets the server load extra expert definitions from a Python file.
- `Server.create(...)` accepts either explicit expert UIDs or generated patterns.
- On CUDA-capable hosts, the server may default to GPU execution unless you request `--device cpu`.

## Good follow-up questions

- "How do I host experts and connect to them remotely?"
- "How do I register a custom expert class?"
- "How do I fetch experts from the DHT?"
- "Why does `hivemind-server` say an expert is missing?"
- "How do I checkpoint expert state?"
