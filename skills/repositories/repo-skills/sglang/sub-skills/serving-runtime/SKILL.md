---
name: serving-runtime
description: "Launch and debug SGLang serving runtime, OpenAI-compatible APIs,
  server arguments, cache/scheduler behavior, parallelism, and production
  serving caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving Runtime

Use this sub-skill for `sglang serve`, `launch_server.py`, `ServerArgs`, HTTP/OpenAI-compatible endpoints, tokenizer/engine settings, tensor/data/expert parallelism, radix/KV cache, speculative decoding, disaggregation, and server runtime failures.

Start by separating argument parsing, model/tokenizer loading, CUDA visibility, backend dependency availability, and request-shape errors. Avoid recommending a full server run unless the environment has the pinned SGLang runtime dependencies installed.

## Cross-Links

- Root routing: `../../SKILL.md`
- Workflow map: `../../references/workflow-map.md`
- Cross-cutting troubleshooting: `../../references/troubleshooting.md`
