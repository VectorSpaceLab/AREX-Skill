# Bundled OmniLive Gradio/FastAPI Entrypoints

This directory packages the OmniLive Gradio frontend plus the three FastAPI backend processes (`backend_vs.py`, `backend_llm.py`, and `backend.py`) so the Gradio service path can be launched without the original source checkout.

## Contents

- `backend.sh` — starts the backend trio from this bundle and passes `IXC_OMNILIVE_MODEL_ROOT` instead of creating source-checkout symlinks.
- `backend_vs.py` — video-memory service on port `8002`; patched to use `IXC_OMNILIVE_MODEL_ROOT`/`IXC_OMNILIVE_MEMORY_MODEL_PATH`, optional bind/port environment variables, and the source syntax fix in `tokenizer_image_token`.
- `backend_llm.py` — MLLM service on port `8001`; patched to use `IXC_OMNILIVE_MODEL_ROOT`/`IXC_OMNILIVE_MLLM_MODEL_PATH` and configurable sibling-service hosts/ports.
- `backend.py` — ASR/TTS service on port `8000`; patched to use `IXC_OMNILIVE_MODEL_ROOT`/`IXC_OMNILIVE_AUDIO_MODEL_PATH` instead of a source-local absolute model path.
- `frontend.py` and `launch_frontend.sh` — Gradio client UI for video/audio streaming.
- `configs_vs/`, `SimHei.ttf`, `girl_01_ref.wav`, and `silence.wav` — support modules/assets needed by the bundled scripts.

## Execution gates

This is a real service bundle. Running it loads multiple models, may download TTS/vocoder assets depending on the environment, opens local ports `8000`, `8001`, `8002`, and then launches a Gradio UI. Confirm CUDA, model components, ports, microphone/camera policy, and network exposure first. If the environment is offline, pre-provide TTS assets with `IXC_OMNILIVE_VOCODER_PATH`, `IXC_OMNILIVE_F5_TTS_CKPT`, and `IXC_OMNILIVE_TTS_REF_AUDIO`.

## Examples

```bash
# From this directory after model layout validation.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b CUDA_VISIBLE_DEVICES=0 ./backend.sh

# LAN-visible backend variant. Keep sibling-service hosts local to the backend box.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b \
IXC_OMNILIVE_BACKEND_BIND_HOST=0.0.0.0 \
IXC_OMNILIVE_ASR_HOST=127.0.0.1 IXC_OMNILIVE_VS_HOST=127.0.0.1 \
CUDA_VISIBLE_DEVICES=0 ./backend.sh

# In a second shell, launch the Gradio frontend against the backend host.
BACKEND_IP=127.0.0.1 AUDIO_SOURCE=gradio VIDEO_SOURCE=local ./launch_frontend.sh
```

For remote backends, set `BACKEND_IP` to a frontend-reachable host. Do not use `0.0.0.0` as a browser/client destination. Optional backend variables: `IXC_OMNILIVE_ASR_PORT`, `IXC_OMNILIVE_LLM_PORT`, `IXC_OMNILIVE_VS_PORT`, `IXC_OMNILIVE_ASR_HOST`, `IXC_OMNILIVE_VS_HOST`, `IXC_OMNILIVE_VOCODER_PATH`, `IXC_OMNILIVE_F5_TTS_CKPT`, and `IXC_OMNILIVE_TTS_REF_AUDIO`.
