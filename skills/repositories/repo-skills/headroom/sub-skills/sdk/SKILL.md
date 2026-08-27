---
name: sdk
description: "Use Headroom compression APIs, SharedContext, relevance and image
  helpers, and the TypeScript SDK in application code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Headroom SDK

Use this sub-skill when the user wants to call Headroom from Python or TypeScript code, embed compression in an application, or understand the SDK-level APIs that do not require operating the proxy or durable memory workflows.

## Route here for

- Python direct compression: `compress`, `compress_spreadsheet`, `CompressConfig`, `CompressResult`, `HeadroomClient`, `ChatCompletions`, `Messages`, and `validate_setup`/metrics helpers.
- `SharedContext` for compressed inter-agent handoffs.
- Relevance and image helpers: `headroom.relevance`, `headroom.image`, and optional extras that affect those APIs.
- TypeScript SDK usage from `sdk/typescript/`, including `compress`, `HeadroomClient`, `simulate`, `retrieve`, `SharedContext`, hooks, format conversion, and path helpers.
- App/framework recipes: OpenAI, Anthropic, LiteLLM, Vercel AI SDK, LangChain, MCP tool outputs, spreadsheet/tabular compression, and other local integration patterns.

## Route elsewhere

- Proxy base URL, `headroom proxy`, and agent wrapping/setup: use `../proxy-wrap/SKILL.md`.
- Memory persistence, MCP registration, learn, and recovery: use `../memory/SKILL.md`.
- Install/update/deployment lifecycle and broad operator diagnostics: use `../ops/SKILL.md`.

## Fast start

Python local compression:

```python
from headroom import compress

result = compress([
    {"role": "user", "content": "Explain this file"},
], optimize=False)
```

Python configuration or app wrapper:

```python
from headroom import CompressConfig
from headroom.client import HeadroomClient
```

TypeScript SDK:

```typescript
import { compress, HeadroomClient, SharedContext } from "headroom-ai";
```

For a safe smoke check, read the bundled helper and run the small no-network validation it documents:

```bash
python scripts/compress_smoke.py --json
```

## References and helpers

- `references/api-reference.md` captures the verified Python API shapes and important defaults.
- `references/typescript-sdk.md` summarizes the TS exports and app-facing examples.
- `references/workflows.md` gives concrete Python and TypeScript application recipes.
- `references/troubleshooting.md` covers missing extras, proxy assumptions, ONNX/HF/image issues, and type/runtime mismatches.
- `scripts/compress_smoke.py` runs a safe no-network Python compression smoke.
- `scripts/tabular_compression_demo.py` is the bundled table/spreadsheet demo adapted from the repo example.

## Safety rules

- Do not promise live proxy behavior when `optimize=False` or when the user has not configured a running proxy.
- Avoid claiming GPU or cloud behavior unless the user explicitly selected the required extras or backend and the environment was verified.
- Do not put private environment paths, tokens, or provider credentials in examples.
- If a feature depends on an optional extra, say so explicitly and show the smallest import path or smoke check that proves it.
