---
name: multimodal-i-o
description: "Use GenAI Processors audio, video, PDF, web, file, and speech connectors."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Multimodal I/O

Use this sub-skill when the task is about getting content into or out of a
processor pipeline: microphones, speakers, cameras, screens, PDFs, URLs,
GitHub, Google Drive, files, speech recognition, speech synthesis, VAD, and
realtime media flow.

## Read when

- The task names `PyAudioIn`, `PyAudioOut`, `VideoIn`, `AudioToWav`, `Vad`,
  `SpeechToText`, `TextToSpeech`, `PDFExtract`, `UrlFetch`, `GithubProcessor`,
  `Drive`, `RateLimitAudio`, `EventDetection`, `add_timestamps`, `to_timestamp`, or `Window`.
- The task is about MIME types, audio sample rates, video frames, PDFs, URLs,
  files, or Google Workspace documents.
- The task needs a realtime audio/video pipeline before or after a model
  wrapper.
- The task needs optional dependency or device troubleshooting.

## Boundaries

This sub-skill owns connectors and media/document processing. It does not own
model selection or function-calling strategy; use `../model-backends/` for
that. It does not own complete app/demo layout; use `../examples-and-apps/` for
full CLIs and AI Studio applets.

## Workflow checklist

1. Identify source modality: terminal text, audio, camera/screen frames, file
   glob, PDF bytes, URL, GitHub URL, Drive doc/sheet/slide, or tool output.
2. Confirm MIME type and substream expectations before composing with model
   processors.
3. Verify optional imports with `scripts/smoke_io.py` before using devices or
   credentials.
4. For audio/video, check device permissions and prefer headphones unless using
   browser echo cancellation.
5. For Google Speech/TTS or Drive, validate credentials and project/service
   setup before running full pipelines.
6. For URLs/GitHub/PDFs, separate safe parser/import smoke from network or file
   reads.
7. When combining with live/realtime models, cross-check trigger and substream
   behavior in `../model-backends/`.

## References and scripts

- `references/api-reference.md` lists connector classes and processor roles.
- `references/workflows.md` provides audio, video, PDF, URL, Drive/GitHub, and
  realtime media patterns.
- `references/troubleshooting.md` covers PortAudio, device permissions,
  Google Cloud auth, PDF rendering, OpenCV/AV, and web fetch failures.
- `scripts/smoke_io.py` imports optional I/O modules without opening devices,
  making network requests, or requiring credentials.

## Native evidence anchors

Evidence comes from source modules under `genai_processors/core/`, docs under
`documentation/docs/development/` and `documentation/docs/concepts/realtime.md`,
and tests including `audio_test.py`, `rate_limit_audio_test.py`,
`speech_to_text_test.py`, `text_to_speech_test.py`, `vad_test.py`,
`video_test.py`, `pdf_test.py`, `web_test.py`, `github_test.py`,
`drive_test.py`, `filesystem_test.py`, `event_detection_test.py`,
`timestamp_test.py`, and `window_test.py`.

## Usability checkpoints

A good answer using this sub-skill should:

- Name exact optional packages and environment variables before runnable code.
- Avoid opening microphones, speakers, cameras, browsers, or remote services in
  a smoke check.
- Preserve non-text parts until a downstream processor intentionally converts
  them.
- Include concrete MIME types and substream names when they affect routing.
- Route model-specific or applet-specific follow-up work to the proper sibling
  sub-skill.
