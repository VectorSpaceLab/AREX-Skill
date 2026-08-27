---
name: deployment-serving
description: "Use PaddleSpeech server/client, HTTP and WebSocket APIs, offline
  and streaming configs, Paddle Inference, ONNX, C++ runtime, and deployment
  troubleshooting safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment and Serving

Use this sub-skill for `paddlespeech_server`, `paddlespeech_client`, PaddleSpeech Serving config YAML, HTTP REST APIs, WebSocket streaming ASR/TTS, online TTS, ACS, Paddle Inference/static models, ONNX streaming, C++ runtime, mobile/ARM deployment orientation, and service troubleshooting.

## Safe Serving Workflow

1. Inspect the config before launch:

   ```bash
   python scripts/inspect_server_config.py --config application.yaml
   ```

2. Confirm side effects: server startup downloads/warmups models, opens ports, and runs until stopped.
3. Start only after approval:

   ```bash
   paddlespeech_server start --config_file application.yaml
   ```

4. Use the matching client:

   ```bash
   paddlespeech_client asr --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
   paddlespeech_client tts --server_ip 127.0.0.1 --port 8090 --input "您好" --output output.wav
   paddlespeech_client tts_online --server_ip 127.0.0.1 --port 8092 --protocol http --input "您好" --output output.wav
   ```

## Route by Deployment Surface

- **Offline HTTP ASR/TTS/CLS/TEXT/VECTOR/ACS**: read `references/server-and-streaming.md` and `references/api-contracts.md`.
- **Streaming ASR**: WebSocket-only ASR endpoint; use a WebSocket config and `paddlespeech_client asr_online`.
- **Streaming TTS**: HTTP or WebSocket depending on `protocol`; online or online-ONNX engine types.
- **Paddle Inference/static**: use static model configs and predictor sections; do not mix dynamic checkpoints.
- **C++/mobile/Android/ARM/FastDeploy**: read `references/runtime-deployment.md`; treat builds as toolchain workflows requiring approval.
- **Audio search / ACS / Milvus apps**: use this sub-skill for service boundaries and external service planning; route embedding details to `../audio-analysis/SKILL.md`.

## References and Helper

- `references/server-and-streaming.md` explains config fields, engine lists, protocols, and client commands.
- `references/api-contracts.md` summarizes REST and WebSocket routes and payload expectations.
- `references/runtime-deployment.md` covers static/Paddle Inference, ONNX, C++ runtime, Android/ARM, Docker, and audio-search boundaries.
- `references/troubleshooting.md` covers ports, host binding, protocol mismatch, engine warmup, and service dependencies.
- `scripts/inspect_server_config.py` safely validates YAML structure without starting a server.

## Do Not Do by Default

- Do not start server processes, Docker Compose, Milvus/MySQL, C++ builds, Android/ARM builds, or streaming demos without approval.
- Do not claim server readiness from CLI help; warmup and model downloads are separate runtime checks.
- Do not use HTTP clients against WebSocket streaming ASR configs or offline configs against online engine types.
