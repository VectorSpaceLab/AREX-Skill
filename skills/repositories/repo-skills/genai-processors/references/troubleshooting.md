# Cross-cutting troubleshooting

## Import and install failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: genai_processors` | package not installed in the active Python | install with `python -m pip install genai-processors`; verify `which python` / `python -m pip show genai_processors` |
| optional module import fails | optional runtime package is missing | install only the required optional package from `references/install.md` |
| `ModuleNotFoundError: pkg_resources` while importing `webrtcvad` | newer `setuptools` distribution omitted `pkg_resources` while `webrtcvad` still imports it | install a compatible setuptools, e.g. `python -m pip install "setuptools<81"`, or use a Conda env whose `webrtcvad` stack includes it |
| `fatal error: portaudio.h: No such file or directory` while installing `pyaudio` | PortAudio headers are absent | use Conda/conda-forge `pyaudio portaudio`, or install system PortAudio development headers before pip-building `pyaudio` |
| `transformers` warns that PyTorch is not found | `transformers` package is present but no `torch` runtime | install a CPU or accelerator-compatible PyTorch build before using `TransformersModel` for real inference |
| example import raises `KeyError: GOOGLE_API_KEY` or `GOOGLE_PROJECT_ID` | some example scripts read env vars at module import time | set the variable before import, or inspect the source without importing the example module |

## Credentials and external services

- `GenaiModel`, Gemini Live API, image generation, and many demos require
  `GOOGLE_API_KEY`. Importing model wrapper modules is safe without the key, but
  constructing/running real model calls is not.
- `SpeechToText` and `TextToSpeech` require Google Cloud project setup,
  credentials, enabled APIs, and `GOOGLE_PROJECT_ID` in the examples.
- `OllamaModel` needs a running Ollama server and a pulled model. Connection
  failures usually mean the service is down, the host is wrong, or the model was
  not pulled.
- MCP examples can use demo, local stdio, or remote HTTP sessions. Remote
  sessions may require headers or API keys; local sessions require the command
  to be installed and trusted.

## Audio, video, and live agents

- Use headphones for microphone/speaker demos. The examples do not implement
  acoustic echo cancellation; browser-based AI Studio applets rely on browser
  echo cancellation.
- `PyAudioIn` / `PyAudioOut` failures usually mean missing PortAudio, missing
  device permissions, or no default input/output device.
- `VideoIn` failures usually mean missing camera/screen permissions, OpenCV/AV
  install issues, or unsupported capture mode.
- Realtime pipelines often use substreams. Ensure audio/video parts use the
  substream expected by the target processor, commonly `realtime`.

## Processor and content mistakes

- Constructing `ProcessorPart` from `bytes` requires an explicit MIME type.
- Accessing `.text` on non-text parts raises. Check `content_api.is_text(part.mimetype)` when a pipeline may contain images, audio, PDFs, function calls, or tool responses.
- `CachedProcessor` buffers the whole input stream before calling the wrapped
  processor. Do not use it where time-to-first-token or infinite streams matter.
- `parallel_concat` preserves concatenated branch order; `streams.merge` yields
  whichever branch produces a part first. Pick the one that matches user-visible
  ordering requirements.
- Live API model names must be Live-capable for `live_model.LiveProcessor`.
  `realtime.LiveProcessor` is the client-side wrapper around any turn-based
  processor and has different trigger behavior.

## Debugging flow

1. Run `python scripts/check_install.py`; add `--optional` only if the task uses
   optional integrations.
2. Confirm required environment variables without printing secret values.
3. For model tasks, run an API-free import/signature check before real requests.
4. For audio/video tasks, verify importability before opening devices.
5. For complex apps, add `trace_file.SyncFileTrace` around the pipeline and inspect the generated trace outside the runtime skill tree.
