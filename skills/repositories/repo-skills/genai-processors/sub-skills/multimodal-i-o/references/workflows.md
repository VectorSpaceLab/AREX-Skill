# Multimodal I/O workflows

## PDF to model content

```python
from genai_processors import content_api
from genai_processors.core import pdf

extract = pdf.PDFExtract()
pdf_part = content_api.ProcessorPart(pdf_bytes, mimetype=pdf.PDF_MIMETYPE)
content = await extract(pdf_part).gather()
```

Pages with images may be rendered as image parts. Preserve those parts if the
model can accept multimodal input; do not call `.text()` unless the task is
text-only.

## URL fetch and cleanup

```python
from genai_processors.core import text, web

pipeline = text.UrlExtractor() + web.UrlFetch(timeout_seconds=10) + text.HtmlCleaner()
```

Treat real URL fetches as network operations. Use import/parser smoke checks in
automation and run actual fetches only when the user/task authorizes network
access.

## Local file glob source

```python
from genai_processors.core import filesystem

source = filesystem.GlobSource(pattern="**/*.md", base_dir="docs")
```

Use bounded globs and avoid passing private or huge directories into model
pipelines by default.

## Speech-to-text into realtime turn processor

```python
from genai_processors.core import audio_io, realtime, speech_to_text, text_to_speech

input_processor = audio_io.PyAudioIn(pya) + speech_to_text.SpeechToText(project_id)
agent = input_processor + realtime.LiveProcessor(turn_processor=model)
```

Use `GOOGLE_PROJECT_ID` and Google Cloud credentials for `SpeechToText`. For a
text-only turn processor, `realtime.AudioTriggerMode.FINAL_TRANSCRIPTION` is
usually the safer trigger.

## Text-to-speech with rate-limited output

```python
from genai_processors.core import rate_limit_audio, text_to_speech

tts = text_to_speech.TextToSpeech(project_id) + rate_limit_audio.RateLimitAudio(sample_rate=24000)
```

Rate limiting keeps generated audio aligned with playback so interruptions can
stop buffered output at the right time.

## Camera or screen input

```python
from genai_processors.core import video

camera = video.VideoIn(video_mode=video.VideoMode.CAMERA, substream_name="realtime")
screen = video.VideoIn(video_mode=video.VideoMode.SCREEN, substream_name="realtime")
```

Camera/screen capture is not a safe import smoke. Check permissions and device
availability before running it.

## Event-driven live commentary pattern

The live commentator example combines:

1. video/audio input on the `realtime` substream,
2. event detection on image frames,
3. Gemini Live API audio output,
4. async function calls for scheduling/interruptions,
5. `RateLimitAudio` before speaker/browser output.

Use this as a design pattern, not as a default smoke test; it needs credentials,
media devices, and a user-facing audio environment.

## Validate without devices

```bash
python sub-skills/multimodal-i-o/scripts/smoke_io.py
```

This imports connector modules and verifies optional package availability
without opening devices or making network calls.
