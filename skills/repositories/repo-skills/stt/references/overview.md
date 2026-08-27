# STT operating overview

## Purpose

STT is a local speech-recognition-to-text app built around `faster-whisper`. It accepts audio or video, converts input to mono 16 kHz WAV with ffmpeg, runs Whisper transcription, and returns plain text, JSON timestamp records, or SRT subtitles.

## Runtime components

- **Server layer:** Flask app served by gevent WSGIServer.
- **Transcription engine:** `faster_whisper.WhisperModel`; models are resolved through the app's model directory and can be downloaded on first use when network is available.
- **Config layer:** runtime settings are parsed from `set.ini` with defaults for local address, language, device type, beam settings, VAD, OpenCC conversion, and model list.
- **Helper layer:** ffmpeg execution, update checks, browser launching, and timestamp formatting live in the helper module.
- **Browser UI:** the template provides multi-file upload, model/language/format selection, progress polling, and export controls.

## Request flow map

### Browser flow

1. User uploads one or more files in the browser.
2. The upload route stores the file under the app's temporary static area and runs ffmpeg to produce a WAV.
3. The process route places a transcription job in an in-memory queue.
4. A background worker loads or reuses the selected Whisper model, transcribes the WAV, converts timestamps, optionally applies OpenCC conversion, and stores the result.
5. The progress route returns progress and final result to the UI.

### Legacy API flow

`POST /api` receives multipart form data with an audio/video `file`, `language`, `model`, and `response_format`. It converts the input with ffmpeg and returns a JSON envelope containing `code`, `msg`, and `data`.

### OpenAI-compatible flow

`POST /v1/audio/transcriptions` receives an OpenAI-like multipart request. It accepts `file`, `model`, `language`, `prompt`, and `response_format`. `srt` returns plain text; `text` returns JSON with a `text` field; `json` returns a JSON list of timestamp records.

## Output formats

- `text`: joined recognized segments with no timestamps.
- `json`: list of `{line, start_time, end_time, text}` records.
- `srt`: numbered subtitle blocks using `HH:MM:SS,mmm --> HH:MM:SS,mmm` timestamps.

## Offline and network behavior

The app is intended for local/offline recognition after dependencies, ffmpeg, and model files are available. First-use model acquisition and the optional update check can touch network resources. If no network should be used, pre-place the needed model folders in the model directory and ignore update-check failures.

## Version notes

The source snapshot used for this skill exposed two version markers: `version.json` said `v0.0.94`, while the runtime UI version constant in the library said `v0.1`. Treat either as a staleness clue and refresh this skill if the source checkout has moved significantly.
