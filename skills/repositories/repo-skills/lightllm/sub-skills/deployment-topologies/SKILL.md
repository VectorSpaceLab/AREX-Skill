---
name: deployment-topologies
description: "Plan LightLLM launch topologies, process sequencing, ports, and
  backend-aware deployment settings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# deployment-topologies

Use this sub-skill when the user needs to launch LightLLM, split it into
prefill/decode or master/config processes, choose ports or GPU assignments, or
understand how the cache and transport layers affect startup.

## Covers

- Single-node and multi-node LightLLM launch topologies.
- `normal`, `prefill`, `decode`, `pd_master`, `config_server`, and
  `visual_only` process roles.
- Port planning, GPU planning, and process start order.
- Multimodal workers, cache settings, and PD-disaggregation coordination.
- MPS, UCX/NIXL/RDMA caveats, and local proxy cleanup for topology scripts.

## Does not cover

- HTTP payload details or endpoint-level request syntax.
- Model-family support decisions or quantization choice.
- Benchmark methodology beyond startup smoke and launch validation.

## Read first

- [references/deployment-matrix.md](references/deployment-matrix.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [../../references/cli-reference.md](../../references/cli-reference.md)
- [../../references/troubleshooting.md](../../references/troubleshooting.md)

## Use this route when the user says

- “how do I run pd_master / prefill / decode?”
- “how should I split GPUs across processes?”
- “what ports and environment variables do I need?”
- “why does the PD topology fail to register?”
- “how do I reason about UCX, NIXL, or MPS for this launch?”

## Minimal working sequence

1. Identify the target topology and the number of GPUs or nodes available.
2. Choose the correct run mode and port layout.
3. Verify proxies, host variables, and cache settings before starting processes.
4. Start the master or scheduler role first when the topology requires it.
5. Launch worker roles only after the coordinating process is ready.
6. Use a tiny request smoke after the topology is up to confirm the route is
   actually serving.

## Decision points

- Use `normal` when a single process is enough.
- Use PD disaggregation only when the workload or model needs it.
- Use `config_server` only when the PD deployment path requires a separate
  registry / configuration service.
- Use `visual_only` for multimodal visual worker cases, not as a general
  serving substitute.
- Do not treat a green health probe as proof that every PD participant has
  joined.

## Related helpers

- `../../scripts/inspect_start_args.py` prints the current run-mode and topology
  related defaults.
- `../../scripts/inspect_cuda.py` confirms the target host can see the expected
  GPU devices.
- `../../scripts/request_smoke.py` can verify a local server once the topology
  is running.

## Troubleshooting highlights

- Port collisions and stale background processes are common during repeated
  launch attempts.
- Proxy settings can break localhost or PD-master traffic.
- The topology may need an explicit host/IP choice; do not guess.
- Missing `nvidia_peermem`, UCX, or transport support can make an otherwise
  correct topology fail at startup.
- Shared memory and cache-size issues often show up only after the processes
  begin talking to each other.

## Review standard

This sub-skill is complete when a future agent can:

- choose a launch topology,
- assign the right processes and ports,
- explain the start order,
- and diagnose the common startup and transport failures without reopening the
  source repository.
