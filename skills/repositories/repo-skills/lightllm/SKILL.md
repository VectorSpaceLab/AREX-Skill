---
name: lightllm
description: "Route LightLLM serving, deployment, and validation workflows into
  bundled references and sub-skills."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LightLLM

LightLLM is a GPU-accelerated LLM serving framework with OpenAI-compatible,
Anthropic-compatible, TGI-style, and LightLLM-native request paths.
Use this skill when a user wants to start the server, understand its HTTP
surface, choose a supported model/backend combination, or validate the runtime
with repo-native benchmark and smoke flows.

## Quick verification

If the package is not already installed, install the public `lightllm`
distribution into a CUDA-capable Python environment first, for example with
`python -m pip install lightllm`, then confirm that the installation is usable.

A healthy inspection environment should be able to do all of the following:

1. Import the installed `lightllm` distribution.
2. Pass `python -m pip check`.
3. Report CUDA readiness from the target environment.
4. Print `python -m lightllm.server.api_server --help`.

Use the bundled helper scripts when you need a fast check:

- `scripts/inspect_cuda.py` for a tiny torch/CUDA smoke.
- `scripts/inspect_start_args.py` for the live `StartArgs` surface.
- `scripts/inspect_api_surface.py` for route and request-schema inspection.
- `scripts/request_smoke.py` for a local `/generate` or `/v1/*` request against a running server.

## Route map

### `serving-api`
Use this sub-skill for HTTP serving, endpoint payloads, streaming, function
calling, reasoning parsers, multimodal requests, health/readiness, metrics,
and profiler control.

Read:
- [sub-skills/serving-api/SKILL.md](sub-skills/serving-api/SKILL.md)
- [references/api-reference.md](references/api-reference.md)
- [references/cli-reference.md](references/cli-reference.md)

### `model-runtime`
Use this sub-skill for supported model families, registry behavior,
quantization/backend selection, multimodal model toggles, reward/RL model
support, and adding a new model support path.

Read:
- [sub-skills/model-runtime/SKILL.md](sub-skills/model-runtime/SKILL.md)
- [sub-skills/model-runtime/references/model-support.md](sub-skills/model-runtime/references/model-support.md)

### `deployment-topologies`
Use this sub-skill for single-node and multi-node launch topologies,
`pd_master` / `prefill` / `decode` layouts, config server flows, multimodal
worker placement, cache modes, RDMA/NIXL/UCX caveats, and startup sequencing.

Read:
- [sub-skills/deployment-topologies/SKILL.md](sub-skills/deployment-topologies/SKILL.md)
- [sub-skills/deployment-topologies/references/deployment-matrix.md](sub-skills/deployment-topologies/references/deployment-matrix.md)

### `benchmark-validation`
Use this sub-skill for repository benchmarks, service throughput/QPS checks,
static inference tests, prompt-cache timing, scenario regressions, and
selected accuracy/validation scripts.

Read:
- [sub-skills/benchmark-validation/SKILL.md](sub-skills/benchmark-validation/SKILL.md)
- [sub-skills/benchmark-validation/references/benchmark-catalog.md](sub-skills/benchmark-validation/references/benchmark-catalog.md)

## Cross-cutting references

- [references/repo-provenance.md](references/repo-provenance.md) records the
  source commit, dirty state, and evidence set.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  captures router placement and selection guidance.
- [references/troubleshooting.md](references/troubleshooting.md) summarizes
  install, import, CUDA, optional dependency, and startup failures that cut
  across sub-skills.

## Runtime notes

- Treat the bundled references and scripts as the public operating context.
  Do not depend on the original checkout remaining available.
- Prefer the smallest workflow that answers the user’s question: serving
  requests go to `serving-api`, model support questions go to `model-runtime`,
  topology and startup sequencing go to `deployment-topologies`, and
  benchmark or regression questions go to `benchmark-validation`.
- For questions that mix multiple areas, start with the sub-skill that owns the
  user-facing action, then read the cross-cutting references above.
- If a workflow needs a running server, use `deployment-topologies` first and
  then return here for the API or benchmark route.
- If a question is about profiler control only, treat it as part of
  `serving-api` and `benchmark-validation`, not as a separate route.

## Staleness check

If the repository version, package version, or supported backend story changes,
refresh the provenance and routing metadata before reusing this skill.
