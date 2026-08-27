---
name: inference
description: "Operate and troubleshoot OpenAssistant inference server, workers,
  text client, safety server, model configs, websocket work protocol, and SSE
  chat flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenAssistant inference sub-skill

Use this sub-skill when a task is about the OpenAssistant local inference stack: the FastAPI inference server, websocket workers, text client, safety server, model configuration selection, chat streaming, plugin calls, GPU sizing, or lightweight `_lorem`/`distilgpt2` smoke checks.

## Route the request

- **Server/worker/chat protocol, debug auth, route map, websocket request/response types, SSE events, plugins, or safety parameters**: read [`references/api-reference.md`](references/api-reference.md).
- **Model config names, `_lorem`, `distilgpt2`, OpenAssistant SFT/RLHF variants, quantization, or GPU memory sizing**: read [`references/model-configs.md`](references/model-configs.md) and run [`scripts/check_inference_config.py`](scripts/check_inference_config.py) when a checkout is available.
- **Local Docker compose inference stack, text client, worker startup, full dev tmux flow, safety server, or load testing**: read [`references/workflows.md`](references/workflows.md).
- **Failures involving API keys, websocket status, protocol upgrade, Redis/Postgres, TGI connection, model downloads, GPU OOM, SSE parsing, plugin OpenAPI, or safety server availability**: read [`references/troubleshooting.md`](references/troubleshooting.md).

## Safe checks

These checks do not download models or start services:

```bash
python scripts/check_inference_config.py --repo-root <repo-root> --model-config _lorem
python scripts/check_inference_config.py --repo-root <repo-root> --model-config distilgpt2 --json
python scripts/check_inference_config.py --repo-root <repo-root> --list
```

Use `_lorem` when the user needs a CPU-only logical smoke path. Use `distilgpt2` only when a tiny Hugging Face model download/cache is acceptable or already available. Real OpenAssistant model configs may require large downloads and GPU memory.

## Boundaries

- Route website chat components, browser-side API calls, and frontend SSE rendering to the `website` sub-skill.
- Route the data-collection backend, task lifecycle, shared REST API client, and OA JSONL exports to the `backend` sub-skill.
- Model training/evaluation/pretokenization, production deployment, Ansible, and infrastructure operations are excluded from this generated skill run.
- Do not run a real model worker, download model weights, use credentials, or start Docker services unless the user explicitly requests it and accepts resource/network requirements.
