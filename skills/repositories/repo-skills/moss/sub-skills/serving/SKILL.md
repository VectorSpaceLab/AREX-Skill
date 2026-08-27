---
name: serving
description: "Routes MOSS serving and UI deployment tasks for FastAPI payloads,
  Gradio or Streamlit demos, session history, and service troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MOSS serving and UI

Use this sub-skill when a task asks how to expose MOSS through an API or UI,
prepare a FastAPI request payload, understand Gradio/Streamlit controls, or
troubleshoot service startup and request handling.

## Read this when

- The user mentions `moss_api_demo.py`, FastAPI, Uvicorn, POST `/`, `uid`,
  `history`, `max_length`, `top_p`, or `temperature`.
- The task asks for a Gradio or Streamlit MOSS chat UI.
- You need a safe curl payload or request template without contacting a server.
- You are debugging port conflicts, JSON request shape, session-history reuse,
  UI dependency imports, CUDA OOM, or slow model loading.

## Route elsewhere

- For prompt syntax and generation parameters, read
  [../inference/SKILL.md](../inference/SKILL.md).
- For model class imports, checkpoint families, quantization, and CUDA smoke,
  read [../model-runtime/SKILL.md](../model-runtime/SKILL.md).
- For fine-tuning or data validation, read
  [../fine-tuning-data/SKILL.md](../fine-tuning-data/SKILL.md).
- For shared installation requirements, read
  [../../references/install-and-dependencies.md](../../references/install-and-dependencies.md).

## Operating workflow

1. **Choose service type.** Use FastAPI when the user needs programmatic POST
   calls; use Gradio for a browser chat demo with sliders; use Streamlit for a
   sidebar-controlled local app. All full services load a MOSS checkpoint and
   require the same model/backend planning as inference.
2. **Prepare request shape before launch.** The FastAPI demo expects JSON fields
   `prompt`, optional `uid`, optional `max_length`, optional `top_p`, and
   optional `temperature`. It returns `response`, `history`, `status`, `time`,
   and `uid`.
3. **Keep state semantics clear.** The API uses `uid` to preserve history; the
   Gradio and Streamlit demos maintain history in UI state. A new or missing
   `uid` starts a fresh API conversation.
4. **Generate safe payloads with the bundled helper.** Run
   [scripts/moss_request_template.py](scripts/moss_request_template.py) to
   validate values and print JSON/curl snippets without contacting a server.
5. **Launch only after model readiness is explicit.** A real service may
   download large checkpoints and allocate GPU memory before accepting requests.
   Check dependencies, model path/cache, GPU selection, and port availability.

## Safe helper example

```bash
python path/to/moss/sub-skills/serving/scripts/moss_request_template.py \
  --prompt "Hello MOSS" --max-length 512 --top-p 0.8 --temperature 0.7 --curl
```

The helper prints a payload and curl snippet. It does not send traffic and does
not require a running MOSS service.

## References

- [references/workflows.md](references/workflows.md) — FastAPI request/response
  schema, UI behavior, startup planning, and validation checklist.
- [references/troubleshooting.md](references/troubleshooting.md) — API, port,
  dependency, CUDA, model download, UI rendering, and state-history failures.
- [scripts/moss_request_template.py](scripts/moss_request_template.py) — safe
  JSON payload/curl generator.

## Answering checklist

- State which demo surface is being used: FastAPI, Gradio, or Streamlit.
- Include the request fields and response fields for API tasks.
- Warn when a command will start a service, download a checkpoint, or allocate
  GPU memory.
- Preserve `uid` when continuing an API conversation; omit or generate it for a
  fresh session.
- Do not claim the server is live unless the task explicitly launched and
  checked it.
