---
name: hugginggpt-chat
description: "Operate HuggingGPT chat orchestration, configuration, API routes,
  web client wiring, endpoint selection, and troubleshooting for JARVIS."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# hugginggpt-chat

Use this sub-skill when a task is about HuggingGPT/JARVIS chat orchestration: CLI or server startup, remote/lite operation, API payloads, the four-stage planning/selection/execution/response loop, configuration files, OpenAI/Hugging Face/Azure credential handling, the web client base URL, token helper behavior, model catalog interpretation, or local endpoint troubleshooting.

Do not use this sub-skill for EasyTool or TaskBench. Route those requests to the sibling `easytool` or `taskbench` sub-skill when available. Treat the full CUDA local model server as optional and unverified unless another verified sub-skill or the user supplies fresh runtime evidence.

## Load the nearest reference

- For what happens during a chat request, API routes, payloads, CLI/server mode, and intermediate results, read [references/chat-orchestration.md](references/chat-orchestration.md).
- For config.default/lite/gradio/azure interpretation, credential resolution, and safe config inspection, read [references/configuration.md](references/configuration.md) and use [scripts/inspect_hugginggpt_config.py](scripts/inspect_hugginggpt_config.py).
- For model catalog coverage, token helpers, Hugging Face versus local endpoints, and ControlNet boundaries, read [references/model-and-endpoint-reference.md](references/model-and-endpoint-reference.md).
- For Vue/Vite web client setup, API base URL, npm scripts, ChatGPT toggle, and browser-side failures, read [references/web-client.md](references/web-client.md).
- For symptom-driven fixes, especially placeholder keys, lite versus hybrid mode, unavailable local endpoints, ControlNet in remote mode, heavy server imports, ffmpeg, and web base URL problems, read [references/troubleshooting.md](references/troubleshooting.md).

## Operating rules

1. Prefer `config.lite.yaml` and `inference_mode: huggingface` for low-footprint remote operation when the user has not explicitly requested local CUDA models.
2. Always check whether OpenAI, Hugging Face, or Azure values are placeholders before recommending server or CLI execution. Environment variables can satisfy OpenAI and Hugging Face credentials, but Azure fields are read from config in the source implementation.
3. Distinguish the three chat surfaces:
   - CLI mode: interactive loop, no per-request dynamic endpoint fields.
   - Server mode: `/hugginggpt`, `/tasks`, and `/results` POST routes.
   - Web client: browser UI that calls the server route and has its own ChatGPT-only fallback path.
4. Never claim the full local `models_server.py` CUDA/model-download stack has been verified by this skill. Document it as an optional path that requires separate environment, model, and hardware validation.
5. For canny/openpose/depth/hed/mlsd/scribble/seg ControlNet tasks in `inference_mode: huggingface`, explain that the source chat server reports ControlNet as local-only instead of promising remote Hugging Face support.
6. Do not expose credential values in advice, logs, pasted config summaries, or script output.

## Quick safe inspection

From this sub-skill directory, run the bundled helper against a JARVIS checkout with a chosen config name:

```bash
python scripts/inspect_hugginggpt_config.py --repo-root <jarvis-repo-root> --config-name lite
```

Or pass a config path directly:

```bash
python scripts/inspect_hugginggpt_config.py --config <path-to-config.default.yaml>
```

The helper parses YAML only, performs no network calls, prints no secrets, and does not import the heavy chat or model-server modules.
