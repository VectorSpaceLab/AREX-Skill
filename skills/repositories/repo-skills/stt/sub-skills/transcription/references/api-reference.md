# API reference

This reference covers the legacy `/api` endpoint and the OpenAI-compatible `/v1/audio/transcriptions` endpoint.

## Shared transcription facts

- Both endpoints accept uploaded audio/video files as multipart form data.
- Both endpoints convert the upload to a 16 kHz mono WAV before transcription.
- Model choice comes from the `model` field and is still governed by the backend `set.ini` device and transcription settings.
- `language` can be omitted or set to `auto` for backend auto-detection behavior.
- `response_format` defaults to `srt` on `/api` and `text` on `/v1/audio/transcriptions` when omitted.
- The backend `WhisperModel.transcribe(...)` call is driven by settings such as `beam_size`, `best_of`, `temperature`, `condition_on_previous_text`, `vad_filter`, and `initial_prompt`.

## Legacy `/api`

### Request

- **Method:** `POST`
- **Path:** `/api`
- **Content type:** multipart form data
- **Required field:** `file`
- **Common fields:**
  - `model`: model name from the configured model list.
  - `language`: language code such as `zh`, `en`, `fr`, `de`, `ja`, `ko`, `ru`, `es`, `th`, `it`, `pt`, `vi`, `ar`, `tr`, `hu`, or `auto`.
  - `response_format`: `text`, `json`, or `srt`.

### Response

- Success is always wrapped as JSON:
  ```json
  {"code": 0, "msg": "ok", "data": ...}
  ```
- On failure the server returns `code: 1` for request or processing problems and `code: 2` for unexpected exceptions.
- `data` shape depends on `response_format`:
  - `text`: a plain transcript string.
  - `srt`: an SRT subtitle string.
  - `json`: a JSON array of segment objects with `line`, `start_time`, `end_time`, and `text`.

### Notes

- The endpoint saves the uploaded file under its original basename, converts it to a temp WAV, and then runs transcription.
- This endpoint is compatible with simple `requests` calls but is not the OpenAI response schema.

### Client smoke

```bash
python ../scripts/api-smoke.py \
  --endpoint legacy \
  --base-url http://127.0.0.1:9977 \
  --file sample.wav \
  --model tiny \
  --language auto \
  --response-format json
```

## OpenAI-compatible `/v1/audio/transcriptions`

### Request

- **Method:** `POST`
- **Path:** `/v1/audio/transcriptions`
- **Content type:** multipart form data
- **Required field:** `file`
- **Accepted fields:**
  - `model`: model name from the configured list.
  - `language`: language code or `auto`.
  - `prompt`: optional prompt text passed through to transcription.
  - `response_format`: `text`, `json`, or `srt`.

### Response

- `response_format=srt` returns `text/plain`.
- `response_format=text` returns JSON shaped like `{"text": "..."}`.
- `response_format=json` returns a JSON array of subtitle segment objects.
- Errors are returned as JSON objects with an `error` field and an HTTP error status.

### Notes

- The handler checks that `ffmpeg` and `ffprobe` are available on `PATH` before processing.
- The uploaded filename is sanitized with `secure_filename` before the temp files are created.
- For OpenAI clients, the `response_format` choice changes the expected response type, so do not assume every call returns JSON text.

### OpenAI-style Python sketch

```python
from openai import OpenAI

client = OpenAI(api_key="local-placeholder", base_url="http://127.0.0.1:9977/v1")
with open("sample.wav", "rb") as audio:
    result = client.audio.transcriptions.create(
        model="tiny",
        file=audio,
        response_format="text",
    )
print(result.text)
```

## Minimal client expectations

- For raw `requests`, send multipart form data and read the response according to the selected `response_format`.
- For OpenAI-compatible clients, use the `/v1` base URL and `client.audio.transcriptions.create(...)`.
- Do not expect `/api` to return the OpenAI `text` wrapper or `/v1` `srt` to return JSON.
- If the user wants a reusable smoke test, use [../scripts/api-smoke.py](../scripts/api-smoke.py).
