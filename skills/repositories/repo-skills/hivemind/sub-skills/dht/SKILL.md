---
name: dht
description: "Routes Hivemind DHT workflows for starting peers, storing and
  fetching records, and debugging multiaddress connectivity."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hivemind DHT

Use this route when the task is about `hivemind.DHT`, `hivemind.dht.DHTNode`, peer discovery, record storage, bootstrap peers, relay settings, or the `hivemind-dht` command.

## Include

- Creating a first DHT node or joining an existing swarm.
- Storing and fetching DHT records, including `subkey` records and expiring values.
- Custom `run_coroutine(...)` logic that runs inside the DHT process.
- Validators, signed records, peer identity, and bootstrap/connectivity debugging.
- Multiaddress choices for `host_maddrs`, `announce_maddrs`, `initial_peers`, `client_mode`, `use_relay`, `use_auto_relay`, and `use_ipfs`.
- The `hivemind-dht` console command.

## Exclude

- Collaborative averaging, optimizers, gradient/state sharing, and compression strategy selection; route those to `collaborative-training`.
- Hosted experts, remote expert clients, and MoE routing; route those to `moe`.
- Benchmarks and CI-only connectivity experiments.

## Start here

1. Read [`references/api-reference.md`](references/api-reference.md) for the verified signatures and key options.
2. Read [`references/workflows.md`](references/workflows.md) for step-by-step DHT setup and store/get examples.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when bootstrap, relay, or identity errors appear.
4. Run [`../../scripts/check_install.py`](../../scripts/check_install.py) from the generated skill tree to confirm the installed package and CLI entry points.

## What to remember

- `hivemind.DHT(start=True)` starts a background DHT process.
- The first peer normally exposes local-loopback multiaddrs; add `host_maddrs` and `announce_maddrs` for externally reachable peers.
- `store(..., expiration_time=...)` and `get(..., latest=...)` are the common record operations.
- Use `run_coroutine(...)` for custom DHT-side logic, but do not call the external DHT interface from inside the DHT process itself.
- For restrictive firewalls or NAT, prefer `client_mode=True`, relay options, or `use_ipfs=True` depending on the deployment.

## Good follow-up questions

- "How do I start a DHT node and print the peer addresses?"
- "How do I connect two Hivemind peers?"
- "Why does DHT startup fail with my bootstrap peers?"
- "How do I store and read a record from the DHT?"
- "How do I make a peer reachable across the internet?"
