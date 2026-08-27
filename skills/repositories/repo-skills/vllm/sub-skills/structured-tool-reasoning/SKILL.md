---
name: structured-tool-reasoning
description: "Use this vLLM sub-skill for structured outputs, JSON/regex/grammar
  constraints, tool calling, reasoning parsers, chat-template/tool-parser
  routing, streaming tool-call deltas, and parser/backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Structured Tool Reasoning

Use this sub-skill when the task involves constrained generation, OpenAI-compatible `response_format` or `structured_outputs`, tool/function calling, reasoning parser output, or debugging parser/template/backend behavior in vLLM.

## Route by Task

- For JSON schema, JSON object, choice, regex, grammar, or structural-tag constraints, read [references/structured-outputs.md](references/structured-outputs.md).
- For OpenAI-compatible `tools`, `tool_choice`, auto tool choice, strict tool schemas, parser names, chat templates, and streaming tool-call assembly, read [references/tool-calling.md](references/tool-calling.md).
- For `--reasoning-parser`, `reasoning` fields, reasoning streaming deltas, thinking controls, and combining reasoning with tools or structured outputs, read [references/reasoning-parsers.md](references/reasoning-parsers.md).
- For unsupported schema keywords, invalid grammars, backend dependency issues, parser name mismatches, incompatible chat templates, missing streamed tool calls, or absent reasoning content, read [references/troubleshooting.md](references/troubleshooting.md).

## Safe Local Helper

Use the bundled validator before contacting a server when a user provides a request fragment:

```bash
# From this sub-skill directory:
python scripts/validate_structured_request.py --input request.json
python scripts/validate_structured_request.py --example tool-streaming

# From the root vLLM skill directory:
python sub-skills/structured-tool-reasoning/scripts/validate_structured_request.py --input request.json
```

The helper checks request-shape consistency for `response_format`, `structured_outputs`, `tools`, `tool_choice`, reasoning flags, common backend compatibility risks, and streaming tool-call handling. It does not import vLLM, download models, start a server, execute tools, or call external APIs.

## Boundaries

- Route general server startup, authentication, host/port, OpenAI endpoint coverage, and deployment layout to `../openai-serving/` when present.
- Route basic `LLM.generate` or `LLM.chat` setup without structured constraints to `../offline-inference/` when present.
- Route multimodal, pooling, embeddings, adapters, and LoRA-specific requests to `../modalities-adapters-pooling/` when present.
- Route performance tuning of structured decoding backends, throughput, batching, and benchmark questions to `../deployment-performance/` when present.

## Hardware and Runtime Notes

- Offline and serving examples require user-provided models and hardware appropriate for the selected model; CPU-only or precompiled inspection environments prove imports and signatures, not GPU throughput.
- OpenAI-compatible examples assume the user already has a running vLLM server exposing `/v1`.
- Tool execution is always application-owned: vLLM returns tool-call names and argument strings; caller code validates and executes the actual functions.
