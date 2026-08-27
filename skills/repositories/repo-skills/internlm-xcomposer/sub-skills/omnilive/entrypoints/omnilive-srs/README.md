# Bundled OmniLive SRS + JavaScript Frontend Entrypoints

This directory packages the source OmniLive SRS-style interactive demo pieces so the workflow can be launched from the generated skill tree without the original checkout.

## Contents

- `backend_ixc/` — FastAPI backend package. `start.sh` is patched to require `ROOT_DIR`/`IXC_OMNILIVE_MODEL_ROOT` instead of a source-local absolute path. `client.py` is patched to read `SRS_RTMP_BASE` for the stream URL.
- `Frontend/` — React/Vite browser frontend. `src/config/service-url.ts` and `vite.config.ts` are patched to accept `VITE_CHAT_SOCKET_URL`, `VITE_SRS_BASE_URL`, and `VITE_SRS_API_URL`.
- `run_srs_docker.sh` — launches the SRS Docker container with the documented ports.
- `run_backend.sh` — launches the FastAPI backend on `HOST`/`PORT` with the selected model root.
- `run_frontend_dev.sh` — launches the Vite dev server with build-time service URLs.

Large example videos and package install outputs are intentionally not bundled. Model weights are never bundled; provide a local model root containing `audio/`, `memory/`, and `merge_lora/`.

## Execution gates

This is a real networked demo. It may run Docker/SRS, bind TCP/UDP ports, start a FastAPI service, install/use Node dependencies, load multiple CUDA models, and access camera/microphone streams. Confirm LAN/firewall/port policy and model availability before execution. If the TTS path is configured to F5-TTS in `backend_ixc/main.py`, pre-provide offline assets with `IXC_OMNILIVE_VOCODER_PATH` and `IXC_OMNILIVE_F5_TTS_CKPT` or allow the documented TTS download.

## Example sequence

```bash
# 1. Start SRS on the LAN-visible SRS host.
CANDIDATE=192.168.3.10 ./run_srs_docker.sh

# 2. Start backend on the GPU host. SRS_RTMP_BASE must point to the SRS RTMP stream prefix.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b SRS_RTMP_BASE=rtmp://192.168.3.10:1935/live/livestream HOST=0.0.0.0 PORT=7862 ./run_backend.sh

# 3. Start frontend dev server. Values are browser-visible URLs.
VITE_CHAT_SOCKET_URL=ws://192.168.3.20:7862/chat VITE_SRS_BASE_URL=webrtc://192.168.3.10/live/livestream VITE_SRS_API_URL=http://192.168.3.10:1985 ./run_frontend_dev.sh
```

Use LAN/routable hostnames. Do not use `127.0.0.1` or `0.0.0.0` as browser destination URLs unless the browser is on the same host and the URL is intentionally local.
