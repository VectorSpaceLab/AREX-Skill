# Serving Topology

Read this when a user wants to expose Otter generation through controller/worker/Gradio services or a direct local CLI. The commands below are distilled from Otter serving code and docs; they are templates for a target Otter checkout or equivalent deployment packaging, not commands that depend on the skill-generation checkout.

## Three-process demo topology

Otter's web demo is a FastAPI/Gradio topology:

1. **Controller** keeps worker status, dispatches requests by `shortest_queue` or `lottery`, and proxies `/worker_generate_stream` to a registered worker.
2. **Model worker** loads an Otter or Flamingo checkpoint, preprocesses images/video frames, streams generated text, registers with the controller, and sends heartbeats.
3. **Gradio web server** asks the controller for available models, collects image/video and text input, and streams model responses through the controller.

Generate a safe command set with the bundled helper instead of hand-copying stale flags:

```bash
python scripts/build_serving_commands.py \
  --checkpoint luodian/otter-9b-hf \
  --model-name otter \
  --controller-port 10000 \
  --worker-port 40000 \
  --gradio-port 7861 \
  --num-gpus 2 \
  --load-bit bf16
```

The generated commands follow this shape when run from a target Otter checkout:

```bash
python -m pipeline.serve.controller --host 0.0.0.0 --port 10000 --dispatch-method shortest_queue
python -m pipeline.serve.model_worker --host 0.0.0.0 --port 40000 --worker_address http://localhost:40000 --controller_address http://localhost:10000 --model_name otter --checkpoint_path luodian/otter-9b-hf --num_gpus 2 --load_bit bf16
python -m pipeline.serve.gradio_web_server --host 127.0.0.1 --port 7861 --controller_url http://localhost:10000
```

For video UI, replace the final module with `pipeline.serve.gradio_web_server_video` and usually use a different port.

## Direct local CLI

`pipeline.serve.cli` is a text-generation CLI for Hugging Face causal language models. It is not the multimodal Otter worker path. It accepts:

- `--model-name` (default `facebook/opt-350m`)
- `--num-gpus` (`1`, an integer, or `auto`)
- `--device` (`cuda` or `cpu`)
- `--conv-template` (conversation template key, default `v1`)
- `--temperature`, `--max-new-tokens`, `--debug`

Use it only when the user is debugging local text generation or conversation template behavior, not when they need image/video Otter input.

## Controller choices

Controller CLI fields:

| Flag | Meaning |
|---|---|
| `--host` | Bind host; default `localhost`. |
| `--port` | Controller port; default `21001`. |
| `--dispatch-method` | `shortest_queue` or `lottery`; default `shortest_queue`. |

Controller endpoints include `/register_worker`, `/refresh_all_workers`, `/list_models`, `/get_worker_address`, `/receive_heart_beat`, `/worker_generate_stream`, and `/worker_get_status`.

## Worker model loading choices

Worker CLI fields:

| Flag | Meaning |
|---|---|
| `--host`, `--port` | Uvicorn bind host/port for this worker. |
| `--worker_address` | Public URL the controller should use for this worker. |
| `--controller_address` | Controller URL. |
| `--lm_path` | Language-model path argument retained in the constructor; model load primarily uses `--checkpoint_path`. |
| `--model_name` | Registry/display model name reported to the controller. |
| `--checkpoint_path` | Otter or Flamingo checkpoint path/model id. If the value contains `otter`, the worker loads `OtterForConditionalGeneration`; otherwise it loads `FlamingoForConditionalGeneration`. |
| `--num_gpus` | `0` for CPU, positive integer for CUDA. GPU mode calls `.cuda()`. |
| `--limit_model_concurrency` | Async semaphore size; default `5`. |
| `--stream_interval` | Retained flag; generation streamer controls actual chunks. |
| `--load_bit` | One of `fp16`, `bf16`, `int8`, `int4`, `fp32`. |
| `--no_register` | Start worker without controller registration. |
| `--load_pt` | Present in CLI but not meaningfully used by the current `load_model` branch. |

`fp16` and `bf16` set `torch_dtype`; `int8` and `int4` request quantized loading; `fp32` uses default dtype. Quantized modes need compatible `transformers`/bitsandbytes-style support and should be tested before public deployment.

## Gradio UI choices

Image and video web servers share most flags:

| Flag | Meaning |
|---|---|
| `--host` | Bind host, default `127.0.0.1`. |
| `--port` | UI port, default `7861`. Use a different port for video UI. |
| `--controller_url` | Controller URL; default `http://localhost:21001`. |
| `--concurrency_count` | Gradio queue concurrency; default `16`. |
| `--model_list_mode` | `once` or `reload`; image UI defaults to `reload`, video UI defaults to `once`. |
| `--share` | Gradio share tunnel. |
| `--moderate` | Enables OpenAI moderation checks; requires `OPENAI_API_KEY`. |
| `--embed` | Builds embedded-mode UI. |

## Dependency and version notes

The serving docs warn that new Gradio/Gradio Client versions can break the demo. The documented local serving environment pinned `gradio==4.7.1` with matching FastAPI/Uvicorn/Transformers-era dependencies; package metadata allows `gradio>=3.33.1`, and inspection installed `gradio==4.8.0`. If UI code fails on `.update()` or component API changes, pin Gradio close to the documented serving version before changing model code.

## Launch readiness checklist

- Confirm the target environment imports `otter_ai` and has the serving dependencies.
- Run `python scripts/check_serving_imports.py` to catch known defects before opening ports.
- Verify checkpoint availability and GPU memory budget; Otter/OpenFlamingo 9B deployments are large and commonly need multiple high-memory GPUs.
- Choose non-conflicting controller, worker, and UI ports.
- Decide whether the service binds only localhost or a public interface.
- Keep `--share` and `--moderate` off unless the user explicitly wants public Gradio sharing or OpenAI moderation.
