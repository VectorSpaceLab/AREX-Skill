# Cross-Cutting Troubleshooting

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: paddle` | PaddlePaddle runtime missing. | Install a compatible `paddlepaddle` or backend-specific PaddlePaddle wheel in the same environment. |
| `ModuleNotFoundError` for `soundfile`, `resampy`, `inflect`, `tiktoken`, `paddlespeech_feat`, or server modules | Full PaddleSpeech runtime dependencies not installed. | Install the missing package set for the selected workflow instead of assuming the source checkout is enough. |
| `cannot import name 'download' from aistudio_sdk.hub` | AIStudio SDK/PaddleNLP compatibility mismatch. | Use an AIStudio SDK version that exposes `aistudio_sdk.hub.download`, or align PaddleNLP and AIStudio SDK versions. |
| `paddlespeech` imports from a checkout instead of installed package | Current directory shadows site-packages. | Test from a neutral directory or install the package into the active environment. |

## CLI and Model Registry Failures

- `paddlespeech stats --task ssl`, `--task whisper`, or `--task kws` may fail as a display issue in this checkout. Use `paddlespeech <task> --help` and the task references; do not assume the command itself is unusable.
- If a model tag is missing, re-check the split between `--model`, `--lang`, `--sample_rate`, `--codeswitch`, `--size`, and task-specific options.
- For ASR code-switch models, `--codeswitch True` is intended for `--lang zh_en` models. Setting code-switch on ordinary zh/en tags can raise an exception.
- For TTS, AM/VOC/lang choices must match; cross-language pairings may fail during resource lookup or frontend execution.

## Audio and Text Input Failures

- Most ASR/ST/SSL/Whisper/vector/KWS models expect WAV input and often 16 kHz sample rate. Use `--yes` only when the CLI should accept automatic resampling/format conversion.
- Long ASR inputs can exceed model-specific max duration limits; split long audio before running recognition.
- Vector score expects exactly two audio paths per score item.
- Shared `.job` parsing does not support text values with spaces for most executors; use direct quoted `--input` for English TTS or other spaced text.
- Punctuation restoration cleans unsupported punctuation and asserts that the remaining text is non-empty. Validate text before model execution.

## Download and Cache Failures

- Set `PPSPEECH_HOME` to a writable directory with enough space.
- Remove incomplete `*_tmp` downloads if md5 checks keep failing after an interrupted download.
- Retry transient CDN/network failures, but do not loop indefinitely on 403/404 or a wrong URL.
- Large model downloads are side effects; ask before starting them when the user did not request actual inference.

## Server Failures

- `paddlespeech_server start` initializes engines and binds a port; inspect the config first.
- If a service starts but clients cannot reach it from a container or remote host, set `host` in the config to a reachable interface address.
- If a port is occupied, change `port` or stop the existing process.
- HTTP configs should not be used for online ASR WebSocket-only engines. Streaming ASR requires WebSocket; streaming TTS can use HTTP or WebSocket depending on config.
- `engine_list` entries must have matching config sections, for example `asr_python` or `tts_online-onnx`.

## Backend and Toolchain Failures

- CUDA is optional for many user workflows. Do not install GPU packages unless the user needs GPU verification or runtime speed.
- Paddle Inference, ONNX, C++ runtime, Android, ARM, Kaldi, MFA, KenLM, OpenFST, Docker, Milvus, and MySQL workflows have extra toolchain or service requirements. Treat them as reference-only until approved.
