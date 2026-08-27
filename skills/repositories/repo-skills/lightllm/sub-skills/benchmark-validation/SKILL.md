---
name: benchmark-validation
description: "Validate LightLLM with repo-native benchmarks, regressions, static
  inference, and smoke flows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# benchmark-validation

Use this sub-skill when the user wants to benchmark LightLLM, compare
throughput or latency, replay a regression scenario, or interpret one of the
repo-native accuracy and performance scripts.

## Covers

- Service benchmarks for throughput, QPS, and multi-turn latency.
- Static inference benchmarks for text and vision models.
- Prompt-cache and PD-related benchmark flows.
- Accuracy / regression / scenario scripts under `test/acc`.
- Log and result-file conventions for repeatable benchmark runs.

## Does not cover

- How to start the server topology itself.
- How to choose a model family or backend.
- Endpoint payload details beyond the smoke request used to warm up a run.

## Read first

- [references/benchmark-catalog.md](references/benchmark-catalog.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [../../references/troubleshooting.md](../../references/troubleshooting.md)
- [../../references/api-reference.md](../../references/api-reference.md)

## Use this route when the user says

- “benchmark LightLLM”
- “measure QPS or latency”
- “run the prompt-cache test”
- “validate the model with the repo benchmark scripts”
- “compare a performance run or regression result”

## Minimal working sequence

1. Confirm the service or deployment route is already up.
2. Choose the smallest benchmark that matches the user’s question.
3. Run a local smoke request before a larger benchmark or scenario script.
4. Record inputs, model path, endpoint, and log directory before collecting
   results.
5. Decide whether the benchmark is throughput-focused, multi-turn, or
   accuracy/regression-focused.

## Decision points

- Use service QPS and latency scripts for serving performance.
- Use static inference scripts for model-side inference timing.
- Use prompt-cache scripts when the user cares about cache reuse.
- Use `test/acc` scripts when the task is regression or scenario validation.
- Keep profiler control in the serving route unless the benchmark itself needs
  profiler coordination.

## Related helpers

- `../../scripts/request_smoke.py` is the small local request used before a
  larger benchmark.
- `../../scripts/inspect_api_surface.py` helps map the benchmark target to the
  right endpoint family.

## Troubleshooting highlights

- The benchmark can start before the service is actually ready.
- `lm_eval` and similar tools may slow down if caches are missing or online
  downloads are allowed unexpectedly.
- Model/tokenizer mismatches often show up as benchmark setup failures rather
  than bad performance numbers.
- A benchmark against the wrong endpoint family gives misleading latency or
  throughput numbers.
- Proxy leakage can make localhost benchmark traffic fail in confusing ways.

## Review standard

This sub-skill is complete when a future agent can:

- pick the correct benchmark family,
- understand the expected logs and summary files,
- run a local smoke before the larger benchmark,
- and explain a suspicious result without reopening the source repository.
