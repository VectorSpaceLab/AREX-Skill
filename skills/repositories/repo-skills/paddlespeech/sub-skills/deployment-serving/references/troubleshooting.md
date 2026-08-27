# Deployment Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Server start hangs or runs forever | Uvicorn service is running normally. | Use explicit process management and stop when done; do not run as a smoke check without timeout. |
| Port already in use | Existing service on config port. | Change `port` or stop the conflicting process. |
| Client cannot reach server from container/remote host | `host` bound to unreachable interface. | Set `host` to a reachable address or use correct container networking. |
| HTTP client against streaming ASR fails | Streaming ASR is WebSocket-only. | Use WebSocket config and `paddlespeech_client asr_online`. |
| Engine section missing | `engine_list` entry has no matching config section. | Add the exact section name or remove the engine. |
| Static inference engine fails | Missing `.pdmodel` / `.pdiparams` or wrong predictor config. | Provide exported static model files and matching predictor fields. |
| Online ONNX TTS fails | Missing ONNX files, onnxruntime, or incompatible block/pad settings. | Verify ONNXRuntime import and model files; start with documented defaults. |
| Full server test downloads too much | Default warmup fetches pretrained models. | Inspect config first; use model paths or approve downloads. |
| Audio search app cannot start | Docker/Milvus/MySQL/config prerequisites missing. | Treat as an external-service deployment project, not a simple PaddleSpeech server command. |
