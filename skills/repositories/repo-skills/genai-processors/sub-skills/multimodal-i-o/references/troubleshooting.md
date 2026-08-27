# Multimodal I/O troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `pyaudio` fails to install with `portaudio.h` missing | PortAudio headers absent | use Conda/conda-forge `pyaudio portaudio` or install system PortAudio dev package before pip build |
| `PyAudioIn`/`PyAudioOut` cannot open device | no default device, permissions, busy device, or wrong sample format | list devices with PyAudio, check OS permissions, close competing apps, choose a supported format |
| model interrupts itself in audio demos | speaker output leaks into mic | use headphones or browser echo cancellation in AI Studio applets |
| `SpeechToText`/`TextToSpeech` auth failure | missing Google Cloud credentials, project ID, or enabled API | set credentials, export `GOOGLE_PROJECT_ID`, enable Speech/TTS APIs, verify billing/quota |
| `webrtcvad` import complains about `pkg_resources` | setuptools version lacks bundled `pkg_resources` | install `setuptools<81` or use a Conda env with compatible stack |
| `VideoIn` cannot open camera/screen | OpenCV/AV issue or device permission | verify `cv2` and `av` imports, check camera/screen permissions, try a shorter test program |
| PDF pages become images instead of text | page contains images or extraction cannot find text | keep image parts for multimodal models or run OCR separately if text is required |
| URL fetch fails | network, timeout, SSL, redirect, or blocked domain | increase timeout deliberately, inspect HTTP status, avoid blind retries, and do not embed credentials in code |
| GitHub or Drive processor cannot fetch | URL parsing, API key, permissions, rate limits | validate URL shape, auth scope, and expected export type before pipeline execution |
| realtime prompt grows too large | long-running stream without compression | use `RollingPrompt`, `Window`, or custom history compression and drop stale media parts |

## Safety rules

- Import checks are safe; device opens, web fetches, Cloud API calls, model calls,
  and local server starts are not smoke checks.
- Keep raw audio/video/PDF data out of logs unless the user explicitly approves.
- Use tiny fixtures when testing extractors or format conversions.
- Preserve MIME types and substreams so downstream processors can route without
  parsing text sentinel tokens.

## Common environment matrix

| Workflow | Required package/service |
| --- | --- |
| local VAD | `webrtcvad` and compatible `setuptools`/`pkg_resources` |
| mic/speaker CLIs | `pyaudio` + PortAudio + device permissions |
| camera/screen/video | `opencv-python`, `av`, device/screen permissions |
| PDF extraction | `pypdfium2`, `Pillow` |
| URL/GitHub fetch | `httpx`, network access, optional API key |
| Drive docs/sheets/slides | Google API client auth and source permissions |
| STT/TTS | Google Cloud Speech/TTS clients, project, credentials, enabled APIs |
