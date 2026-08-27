# Multimodal I/O API reference

## Audio and speech

| API | Purpose | Notes |
| --- | --- | --- |
| `core.audio.AudioToWav` | Buffers audio parts and emits a WAV part | Useful before models that expect one audio file per turn. |
| `core.audio_io.PyAudioIn(pyaudio_instance, ...)` | Source processor for microphone audio | Requires `pyaudio` and an input device; avoid in smoke tests. |
| `core.audio_io.PyAudioOut(pyaudio_instance, ...)` | Plays audio parts to speakers | Requires `pyaudio`; handles interruption-style metadata. |
| `core.speech_to_text.SpeechToText(project_id, recognition_config=None, audio_passthrough=False, with_endpointing=True, strict_endpointing=True, with_interim_results=True, ...)` | Google Cloud streaming STT | Requires Cloud Speech API and credentials/project. Emits endpointing and transcription substreams. |
| `core.text_to_speech.TextToSpeech(project_id, language_code='en-US', voice_name='en-US-Chirp3-HD-Charon', with_text_passthrough=True)` | Google Cloud TTS | Converts text parts to audio parts. |
| `core.vad.Vad` | Local voice activity detector | Requires `webrtcvad`; emits speech event parts. |
| `core.rate_limit_audio.RateLimitAudio` | Rate-limits audio playback | Needed when TTS/model output is faster than natural playback. |

## Video, timestamps, and event detection

| API | Purpose |
| --- | --- |
| `core.video.VideoMode` | Enum for camera versus screen capture. |
| `core.video.VideoIn(...)` | Source processor for camera/screen frames. |
| `core.video.VideoExtract` | Extracts frames from video content using AV/OpenCV. |
| `core.timestamp.add_timestamps` / `to_timestamp` | Adds timing parts to image streams and formats elapsed timestamps for video/realtime context. |
| `core.event_detection.EventDetection` | Uses a model processor to detect visual events and emit event notifications. |
| `core.window.RollingPrompt` and `core.window.Window` | Maintain sliding prompt/history for long-running streams. |

Video modules require `opencv-python` and `av`. Device capture requires actual
permissions and a compatible camera/screen source.

## Documents, web, filesystem, and Drive

| API | Purpose | Notes |
| --- | --- | --- |
| `core.pdf.PDFExtract` | Converts PDF bytes into text or rendered image parts | Requires `pypdfium2` and Pillow; pages with images are rendered. |
| `core.text.UrlExtractor` | Converts URLs in text into `FetchRequest` parts | Pair with `web.UrlFetch`. |
| `core.web.UrlFetch(timeout_seconds=10)` | Fetches URL content using HTTPX | Network operation; safe import but not a smoke check. |
| `core.text.HtmlCleaner` | Strips or converts HTML after fetching | Use after `UrlFetch` for web text. |
| `core.filesystem.GlobSource(pattern, base_dir=...)` | Reads local files matching a glob | Keep file reads bounded and user-approved. |
| `core.github.GithubProcessor` | Fetches GitHub file content from GitHub URLs | Network operation; may use an API key. |
| `core.drive.Docs`, `Sheets`, `Slides` | Fetch Google Docs/Sheets/Slides as PDF or CSV-style parts | Requires Google API setup and permissions. |

## Substream expectations

- Live/realtime media usually goes through substream `realtime`.
- Speech-to-text emits endpointing and transcription substreams; final
  transcription should be retained in prompts only when desired.
- Tool/UI/direct-output substreams should be preserved and routed explicitly;
  do not flatten them into the model prompt accidentally.
