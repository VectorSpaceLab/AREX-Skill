# Server and Streaming Reference

## Config Shape

A PaddleSpeech server config has top-level:

- `host`: bind address.
- `port`: service port.
- `protocol`: `http` or `websocket`.
- `engine_list`: list of `<task>_<engine type>` entries.
- One section per engine entry, for example `asr_python`, `tts_inference`, `text_python`, `vector_python`, `tts_online-onnx`, or `asr_online`.

Offline HTTP config can combine ASR, TTS, CLS, TEXT, and VECTOR engines. Streaming ASR uses WebSocket and online ASR engines. Streaming TTS can use HTTP or WebSocket and online/online-ONNX engines.

## Server Commands

```bash
paddlespeech_server help
paddlespeech_server stats --task tts
paddlespeech_server start --config_file application.yaml --log_file ./log/paddlespeech.log
```

`stats` can display dynamic/static model tables for server-supported tasks. Some server ASR stats may fail as a registry display issue; do not treat that alone as a server install failure.

## Client Commands

Offline HTTP clients:

```bash
paddlespeech_client asr --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
paddlespeech_client tts --server_ip 127.0.0.1 --port 8090 --input "您好" --output output.wav
paddlespeech_client cls --server_ip 127.0.0.1 --port 8090 --input input.wav
paddlespeech_client text --server_ip 127.0.0.1 --port 8090 --input 今天的天气真不错啊
paddlespeech_client vector --task spk --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
paddlespeech_client acs --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
```

Streaming clients:

```bash
paddlespeech_client asr_online --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
paddlespeech_client tts_online --server_ip 127.0.0.1 --port 8092 --protocol http --input "您好" --output output.wav
paddlespeech_client tts_online --server_ip 127.0.0.1 --port 8092 --protocol websocket --input "您好" --output output.wav
```

## Engine Type Notes

- `python`: dynamic Paddle/Python executor path.
- `inference`: Paddle Inference/static model path; requires `.pdmodel` / `.pdiparams` files and predictor config.
- `online`: streaming Python engine.
- `online-onnx`: streaming ONNXRuntime engine.

The engine list and section names must match exactly. If `engine_list` includes `tts_online-onnx`, the config must have a `tts_online-onnx` section.
