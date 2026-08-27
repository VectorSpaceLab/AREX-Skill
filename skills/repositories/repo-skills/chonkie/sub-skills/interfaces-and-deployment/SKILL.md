---
name: interfaces-and-deployment
description: "Use Chonkie's CLI, local FastAPI API, Cloud wrappers, logging, and
  deployment surfaces safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Interfaces and Deployment

Use this sub-skill when the task is about Chonkie's command line interface, the local self-hosted FastAPI API, Chonkie Cloud wrappers, logging/configuration, or serving/deployment. It is optimized for safe local diagnostics and for constructing correct commands or HTTP/API payloads without starting long-lived services or using credentials by default.

## Route first

- For Python `Pipeline().fetch_from().process_with().chunk_with().refine_with().run()` workflows, read `../pipelines-and-processing/`.
- For deterministic local chunker behavior, chunk object fields, tokenizer details, or fallback chunker choice, read `../chunking-and-types/`.
- For model/provider embedding keys and third-party generative/provider credentials, read `../embeddings-and-generative/`.
- For vector database services, handshakes, and storage credentials, read `../integrations-and-storage/`.

## Read the bundled references

- `references/cli-reference.md` for installed `chonkie` commands, flags, parameter parsing, and safe CLI patterns.
- `references/api-and-cloud-reference.md` for local FastAPI routes, request schemas, environment variables, cloud wrapper classes, and deployment guidance.
- `references/troubleshooting.md` for CLI/API/cloud/logging/deployment failure modes and routing decisions.

## Default operating posture

1. Prefer deterministic local CLI examples (`--chunker recursive`, `--chunker token`, or `--chunker sentence`) unless the user explicitly selected semantic/model-backed chunking.
2. Treat `chonkie serve` and `uvicorn chonkie.api.main:app` as long-running commands: explain or run them only when the user asks for a server, and keep smoke checks to imports/help/schema inspection.
3. Treat Chonkie Cloud as optional external API usage. Do not instantiate cloud clients in diagnostics unless `CHONKIE_API_KEY` or an explicit `api_key` is intentionally provided.
4. Keep local API credentials separate from provider credentials: the OSS FastAPI server has no built-in auth; `CHONKIE_API_KEY` is for Chonkie Cloud; embedding provider keys belong to `../embeddings-and-generative/`.
5. For deployment, distill the Docker/compose behavior into guidance and environment requirements; do not require users to read or copy any source checkout file.

## Safe smoke

Run the bundled smoke when validating an installed Chonkie environment:

```bash
python scripts/cli_api_smoke.py
```

If the `chonkie` console command is intentionally unavailable but Python imports should still be checked:

```bash
python scripts/cli_api_smoke.py --skip-cli
```

The smoke only invokes CLI help, imports/inspects the FastAPI app and schemas, and inspects cloud class signatures without starting a server or using credentials.
