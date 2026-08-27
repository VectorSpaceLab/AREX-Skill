# OmniLive Service Deployment Reference

This reference is for planning only. It explains OmniLive service topology and configuration choices without starting listeners. Use `scripts/render_service_plan.py` to produce an editable deployment plan for a concrete host/IP/model-root combination.

## Deployment choices

| Choice | Components | Strengths | Caveats |
| --- | --- | --- | --- |
| SRS + JavaScript frontend + FastAPI backend | Browser frontend, SRS WebRTC/RTMP server, one FastAPI chat backend | Intended for real-time interruption and browser WebRTC push. | Tested only on the same LAN; requires Docker/SRS ports, frontend URL edits, and careful LAN IP selection. |
| Gradio frontend + FastAPI backend trio | Gradio frontend, video-memory service, MLLM service, ASR/TTS service | No SRS server; simpler local demo path. | No real-time interruption support; microphone/local-camera behavior depends on host devices and VAD/echo cancellation. |

Both choices require a complete OmniLive model root. Memory-backed services require `merge_lora/` before launch.

## SRS + JavaScript frontend + FastAPI backend

### Architecture

1. Browser frontend captures camera and microphone with Web APIs.
2. Frontend publishes the audio/video stream to an SRS server through WebRTC. The SRS server converts/raw-relays stream data for backend consumption.
3. FastAPI backend consumes streaming data, runs ASR/audio classification, updates video memory, runs the OmniLive MLLM, and sends text/audio responses back through a WebSocket/chat route.
4. Frontend receives model responses over a chat WebSocket and displays/plays them.

Important service endpoints and ports from the reference implementation:

| Surface | Default | Purpose |
| --- | --- | --- |
| SRS RTMP | TCP `1935` | Stream ingest/RTMP compatibility. |
| SRS HTTP | TCP `8080` | SRS player and HTTP access. |
| SRS API | TCP `1985` | WebRTC publish API; frontend development proxy usually forwards `/rtc` here. |
| SRS WebRTC UDP | UDP `8000` | WebRTC media path. |
| FastAPI chat backend | TCP `7862` | Main chat/WebSocket backend. |
| Frontend dev server | usually `8081` | Browser UI. Actual port is whatever the dev server prints. |

### LAN IP and SRS candidate caveats

- The SRS `CANDIDATE` value must be a LAN-reachable IP address such as `192.168.x.x` or `10.x.x.x`, not `127.0.0.1`.
- The setup was validated with all components in the same local network. Cross-network, NAT, VPN, container bridge, and cloud deployments need extra WebRTC/STUN/TURN/firewall work.
- Open both TCP and UDP ports. A common failure is opening `8080`/`1985` but forgetting UDP `8000`.
- Browser security can block camera/microphone on insecure origins. A local HTTPS/dev certificate or explicit browser exception may be needed.

Bundled SRS launcher:

```bash
cd entrypoints/omnilive-srs
CANDIDATE="192.168.3.10" ./run_srs_docker.sh
```

Equivalent SRS plan:

```bash
export CANDIDATE="192.168.3.10"  # LAN IP, not 127.0.0.1
docker run --rm --env CANDIDATE="$CANDIDATE" \
  -p 1935:1935 -p 8080:8080 -p 1985:1985 -p 8000:8000/udp \
  registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5 \
  objs/srs -c conf/rtc2rtmp.conf
```

### Backend planning

The backend needs an environment with CUDA, OmniLive Python dependencies, the completed model root, and `ROOT_DIR` pointing at that model root. The repaired skill bundles it at `entrypoints/omnilive-srs/backend_ixc/` and provides `run_backend.sh`:

```bash
cd entrypoints/omnilive-srs
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b \
SRS_RTMP_BASE=rtmp://192.168.3.10:1935/live/livestream \
HOST=0.0.0.0 PORT=7862 ./run_backend.sh
```

Equivalent backend command inside `backend_ixc/`:

```bash
export ROOT_DIR=/models/internlm-xcomposer2d5-ol-7b
uvicorn main:app --host 0.0.0.0 --port 7862 --loop asyncio
```

Plan this only after:

```bash
python scripts/check_omnilive_layout.py /models/internlm-xcomposer2d5-ol-7b --workflow service-srs --require-weights
```

If the backend is remote from the browser/frontend:

- Replace the frontend chat URL host with the backend host/IP, for example `ws://BACKEND_IP:7862/chat`.
- Ensure backend CORS/websocket/firewall rules allow the browser origin.
- Ensure the backend can reach the SRS stream URL. The reference client contains hard-coded/host-specific stream URL assumptions; future deployments should make stream URLs configurable rather than relying on local constants.

### Frontend planning

The JavaScript frontend is bundled under `entrypoints/omnilive-srs/Frontend/`. It has two key URLs and one SRS API proxy target:

```ts
CHAT_SOCKET_URL = 'ws://BACKEND_IP:7862/chat'
SRS_BASE_URL = 'webrtc://SRS_IP/live/livestream'
```

The repaired frontend reads build-time environment variables through the wrapper:

```bash
cd entrypoints/omnilive-srs
VITE_CHAT_SOCKET_URL=ws://192.168.3.20:7862/chat \
VITE_SRS_BASE_URL=webrtc://192.168.3.10/live/livestream \
VITE_SRS_API_URL=http://192.168.3.10:1985 \
./run_frontend_dev.sh
```

The development proxy for WebRTC publish requests should point `/rtc` to the SRS API endpoint, for example `http://SRS_IP:1985`. The frontend requires Node.js >= 18 and starts with the equivalent of `npm install` then `npm start`. Always tell users to trust the actual port printed by the dev server.

## Gradio frontend + three FastAPI backend processes

### Architecture

The Gradio deployment does not use SRS. It separates backend work into three processes:

| Process | Default port | Role |
| --- | ---: | --- |
| Video-memory backend | `8002` | Receives image frames, constructs video memory, selects memory for a text query. |
| MLLM backend | `8001` | Receives ASR/user query, asks the video-memory backend for selected frames/memory, runs the merged OmniLive MLLM, streams answer chunks to ASR/TTS backend. |
| ASR/TTS backend | `8000` | Receives audio chunks, runs Swift audio ASR/classification, runs TTS, serves generated audio back to frontend. |
| Gradio frontend | Gradio default unless overridden | Streams video/audio to backend and displays 1 FPS video preview/audio output. |

The reference backend shell starts the video-memory process and MLLM process in the background, then runs ASR/TTS in the foreground. It uses `CUDA_VISIBLE_DEVICES`; with one GPU all three processes share the same visible device.

### Bundled Gradio/FastAPI service bundle

The repaired skill packages a runnable Gradio service bundle at `entrypoints/omnilive-gradio/`. Use it for approved execution instead of source checkout files:

```bash
cd entrypoints/omnilive-gradio
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b CUDA_VISIBLE_DEVICES=0 ./backend.sh
# second shell
BACKEND_IP=127.0.0.1 AUDIO_SOURCE=gradio VIDEO_SOURCE=local ./launch_frontend.sh

# For a LAN-visible backend, bind all three FastAPI services explicitly:
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b \
IXC_OMNILIVE_BACKEND_BIND_HOST=0.0.0.0 \
IXC_OMNILIVE_ASR_HOST=127.0.0.1 IXC_OMNILIVE_VS_HOST=127.0.0.1 \
CUDA_VISIBLE_DEVICES=0 ./backend.sh
```

The bundle includes `backend_vs.py`, `backend_llm.py`, `backend.py`, `frontend.py`, `configs_vs/`, `SimHei.ttf`, `girl_01_ref.wav`, and `silence.wav`. The backend scripts are patched to read `IXC_OMNILIVE_MODEL_ROOT` and related overrides instead of source-local model paths or symlinks. `IXC_OMNILIVE_BACKEND_BIND_HOST` controls FastAPI bind host; `IXC_OMNILIVE_ASR_PORT`, `IXC_OMNILIVE_LLM_PORT`, and `IXC_OMNILIVE_VS_PORT` control ports; `IXC_OMNILIVE_ASR_HOST` and `IXC_OMNILIVE_VS_HOST` control how the MLLM process reaches sibling backend services.

### Model root behavior

The Gradio backend scripts need a complete model root with `audio/`, `memory/`, and `merge_lora/`. A safe production plan is:

1. Validate the actual model root with `check_omnilive_layout.py --workflow service-gradio --require-weights`.
2. Set `IXC_OMNILIVE_MODEL_ROOT=/path/to/internlm-xcomposer2d5-ol-7b` before launching the bundled backend.
3. Keep `merge_lora/`, `memory/`, and `audio/` in the same model root.

### Gradio frontend flags

The Gradio frontend accepts:

```bash
python frontend.py --backend_ip BACKEND_IP --audio_source gradio --video_source local
# or from the repaired bundle:
BACKEND_IP=BACKEND_IP AUDIO_SOURCE=gradio VIDEO_SOURCE=local ./launch_frontend.sh
```

Flags:

| Flag | Values | Behavior |
| --- | --- | --- |
| `--backend_ip` | IP/host string | Host contacted at ports `8000`, `8001`, and `8002`. Use a LAN or routable backend IP for remote backends, not `0.0.0.0` as a client target. |
| `--audio_source` | `gradio` or `local` | `gradio` uses `gr.Audio(..., sources=["microphone"], streaming=True)` and the VAD consumer over streamed chunks. `local` uses PyAudio directly and requires echo cancellation/device-index handling. |
| `--video_source` | `local` or `gradio` | `local` uses OpenCV camera capture and sends snapshots to backend; `gradio` uses a Gradio webcam image stream. The UI preview is only about 1 FPS. |

Audio/VAD behavior:

- The frontend loads a FunASR `fsmn-vad` model to segment speech.
- `audio_source=gradio` buffers incoming microphone chunks and uses VAD end events before sending slices.
- `audio_source=local` records with PyAudio at 16 kHz mono chunks; the reference implementation uses a fixed input device index and warns that echo cancellation must be implemented by the deployer.
- Classification audio is a short pre-speech/context chunk; ASR audio is the detected speech slice.

Remote backend caveats:

- Set `IXC_OMNILIVE_BACKEND_BIND_HOST=0.0.0.0` only when the network exposure is approved; use a LAN/routable host in the frontend `BACKEND_IP`, not `0.0.0.0` as a client target.
- `no_proxy` may need to include backend and local IPs so requests between the three backend processes do not go through a corporate proxy.
- Firewalls must expose all three backend ports to the Gradio frontend host.

## Render a plan safely

```bash
python scripts/render_service_plan.py \
  --mode both \
  --model-root /models/internlm-xcomposer2d5-ol-7b \
  --lan-ip 192.168.3.10 \
  --backend-ip 192.168.3.20 \
  --audio-source gradio \
  --video-source local
```

The helper prints a Markdown plan only. It does not run Docker, uvicorn, npm, Gradio, torch, Swift, or network probes.
