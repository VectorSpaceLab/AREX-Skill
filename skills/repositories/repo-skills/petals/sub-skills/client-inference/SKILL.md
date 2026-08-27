---
name: client-inference
description: "Use Petals client APIs for distributed model loading, generation,
  inference sessions, routing, retries, and swarm selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Petals Client Inference

Use this sub-skill to write, debug, or adapt Petals client code for distributed text generation, model forward passes, sequence classification, speculative Llama generation, inference-session cache reuse, or route/retry controls.

## Route elsewhere

- Server hosting, DHT bootstrap, public/private server commands: `server-swarms`.
- Trainable prompts, deep prompt tuning, optimizer loops: `prompt-tuning`.
- Block conversion, tensor parallel, quantization internals: `distributed-blocks`.
- Benchmark command construction and maintainer test selection: `benchmarks-maintenance`.

## Workflow

1. Read [references/api-reference.md](references/api-reference.md) for entry points, config fields, and constraints.
2. Use [references/workflows.md](references/workflows.md) for generation, private-swarm selection, inference-session, classification, and speculative-generation recipes.
3. Run the safe no-network checker: `python scripts/client_smoke_check.py --pretty`.
4. For route, retry, tokenizer, model access, or session errors, use [references/troubleshooting.md](references/troubleshooting.md).

## Principles

Treat Petals classes as Transformers-compatible wrappers whose embeddings/heads run locally and transformer blocks run on remote servers. Make swarm choice explicit when reproducibility matters. When generating without an active session, pass exactly one of `max_new_tokens` or `max_length`; for interactive continuation, create one `inference_session(max_length=...)` large enough for the entire exchange.
