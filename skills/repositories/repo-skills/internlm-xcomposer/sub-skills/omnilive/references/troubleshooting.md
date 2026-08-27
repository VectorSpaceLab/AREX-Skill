# OmniLive Troubleshooting

## Model layout failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `merge_lora/` missing | `base/` and `adapter/` were downloaded but not merged. | Stop memory/service planning, run a LoRA merge plan, then re-check layout. Do not fall back to `base/` for memory QA. |
| Audio quickstart cannot find processor/config | The path points at the model root or `base/` instead of `audio/`. | Use `/path/to/model-root/audio` for local layouts, or hosted root + `model_dir="audio"` if the loader supports it. |
| Video benchmark cannot load config/tokenizer | The path points at the model root instead of `base/`. | Use `/path/to/model-root/base`. |
| Service MLLM loads base model but memory answers fail | `merge_lora/` was not created or not in the same root as `memory/`. | Validate `--workflow memory --require-weights`; merge first with `entrypoints/omnilive-examples/run_merge_lora.sh`. |
| Layout checker warns about missing weights | The directory is a source/code stub, partial download, or Git LFS checkout without model files. | For real inference, require `*.safetensors`/`*.bin` files. For planning only, record the warning as a gap. |

## Python/runtime dependencies

- Audio: `swift`, torch with CUDA, Qwen2-Audio-compatible transformers/processor dependencies, and ffmpeg for benchmark audio decoding.
- Base/video: `transformers`, `trust_remote_code=True`, torch/CUDA, torchvision, PIL, decord, and sometimes flash-attention for high-resolution use.
- Merge: `peft`, transformers, torch with enough CPU/GPU memory to load base + adapter.
- Memory: `accelerate`, decord, torchvision, PIL, the `memory/` remote-code modules, and CUDA fp16 support.
- Services: FastAPI/uvicorn, requests, queues/threads, OpenCV, FunASR VAD, Swift audio, TTS dependencies, Node.js >= 18 for the JavaScript frontend, and Gradio 5.8.0 for the Gradio frontend.
- TTS: the service may use MeloTTS or F5-TTS. Treat them as service dependencies only; do not debug third-party Melo internals from this sub-skill.

## CUDA and memory

| Symptom | Action |
| --- | --- |
| CUDA OOM during base/video benchmark | Lower `--max-frame`, reduce concurrent chunks per GPU, or use fewer browser/service processes on the same GPU. |
| CUDA OOM during memory video QA | Lower `--max-frame`, shorten the video, or reduce other resident processes. Memory QA loads both `merge_lora/` and `memory/`. |
| Slow or unstable live service | Avoid co-locating all Gradio backend processes with other jobs; pin `CUDA_VISIBLE_DEVICES`; prefer one dedicated GPU for initial service smoke. |
| fp16/bfloat16 error | Match dtype to hardware. The merge recipe uses bfloat16; base quickstarts often use half/fp16 autocast. |

## Memory video QA behavior

- `--vs-thresh` controls local-memory selection. Increase it to reduce irrelevant clips; decrease it when grounding fails despite visible evidence.
- If no local clip passes the threshold, the pipeline falls back to all sampled frames and emits a grounding-failure signal. This is not the same as a model crash; it means the memory selector did not find a confident query-related segment.
- `--max-frame` only caps frames after selection. A high value improves visual coverage but increases the size of the rendered image/contact sheet and VRAM pressure.
- The memory selector uses 16 frames per clip and enforces at least 5 clips for offline QA. Very short videos can still be expanded to the minimum clip count.
- If multiple-choice accuracy is poor, inspect whether options were preserved as `A. ...`, `B. ...` and whether the answer parser expects the first generated character.

## Audio/VAD issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| ASR returns sound description instead of transcript | Audio classification branch may have labeled non-speech or mixed speech/sound. | Confirm the query is ASR, not classification; test with a clean mono 16 kHz WAV; inspect classification output separately. |
| Gradio frontend never sends speech | VAD does not detect an end event or chunks are not int16 PCM-shaped. | Try `--audio_source gradio`, verify microphone permissions, and test a short WAV through the backend endpoint before live streaming. |
| Local microphone echoes model audio | `--audio_source local` lacks echo cancellation by default. | Prefer `gradio` audio source for first deployment or implement OS/browser echo cancellation. |
| PyAudio cannot open device | The reference local path uses a fixed input device index. | Enumerate devices and patch/select the correct input device. |

## SRS and LAN failures

- Never set SRS `CANDIDATE` to `127.0.0.1` for browser clients. Use the LAN IP visible from the frontend browser.
- Same-LAN deployment is the known-good path. Remote/cloud deployment may need STUN/TURN, HTTPS, firewall, and reverse-proxy changes.
- Open TCP `1935`, `8080`, `1985` and UDP `8000` for SRS. UDP `8000` is easy to miss.
- Browser camera/microphone capture can fail on insecure origins. Use localhost exceptions, HTTPS, or browser trust settings.
- If WebRTC publish works in SRS player pages but the app fails, check the frontend SRS URL and the dev proxy target for `/rtc`.

## FastAPI/Gradio service failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Frontend points to `0.0.0.0` and cannot connect | `0.0.0.0` is a bind address, not a client destination. | Set `--backend_ip`/chat URL to a LAN or routable host/IP. |
| Remote Gradio frontend cannot reach backend | Backend scripts may bind to hostname-derived IP and firewall may block ports. | Use the bundled `entrypoints/omnilive-gradio/launch_frontend.sh` with a frontend-reachable `BACKEND_IP`, expose ports `8000`/`8001`/`8002`, and add local IPs to `no_proxy` if proxies intercept internal requests. |
| TTS replies never play | ASR/TTS backend queue empty, TTS dependency missing, or generated audio path not readable. | First test `/transcribe`, then `/recv_llm`, then `/get_audio` with a tiny text response. |
| Video memory never updates | Camera frames are not sent to port `8002` or OpenCV/Gradio video source is inactive. | Click/push video first; confirm frame POSTs reach the video-memory backend. |
| SRS backend works locally but not with remote frontend | Chat WebSocket, SRS WebRTC URL, and SRS API proxy are mixed across hosts. | Use one explicit network diagram; check `CHAT_SOCKET_URL`, `SRS_BASE_URL`, and `/rtc` proxy target together. |

## Planning-only gaps to surface

If any of these are unknown, record them before producing an execution-ready plan:

- model root path and whether `merge_lora/` has real weights;
- GPU count, CUDA version, and whether service and benchmarks can monopolize GPUs;
- whether SRS, frontend, and backend are on one LAN or split across networks;
- audio source (`gradio` vs `local`) and echo-cancellation requirements;
- video source (`local` vs `gradio`) and camera availability;
- benchmark dataset roots, licenses, and expected output/submission format.
