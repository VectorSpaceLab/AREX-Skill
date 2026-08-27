---
name: transcription
description: "Use STT browser uploads, legacy REST API, and OpenAI-compatible
  transcription requests."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# STT transcription

Use this sub-skill after the local server is running. It covers the browser UI, batch upload/export behavior, the legacy `/api` endpoint, the OpenAI-compatible `/v1/audio/transcriptions` endpoint, and response-format parsing.

Do **not** use this sub-skill for dependency installation, model placement, ffmpeg setup, CUDA enablement, or server launch. Route those tasks to [../setup/SKILL.md](../setup/SKILL.md).

## Read when

- The user wants to transcribe audio or video through the browser.
- The user needs a Python/requests/curl/OpenAI-compatible API call.
- The request asks about `response_format=text`, `response_format=json`, or `response_format=srt`.
- The user wants batch uploads, auto export, or individual export behavior.
- The API returns a confusing shape, an error envelope, or an empty result.

## Operating workflow

1. **Confirm the server is running.** If not, go to [../setup/SKILL.md](../setup/SKILL.md) first.
2. **Choose the surface.** Use the browser for manual/batch file work; use `/api` for the repo's legacy JSON envelope; use `/v1/audio/transcriptions` for OpenAI-style clients.
3. **Choose language and model.** Use `auto` or an explicit language code. Models ending in `.en` are for known-English audio.
4. **Choose response format.** `text` is plain recognized text, `json` is timestamp records, and `srt` is subtitle text.
5. **Validate with the bundled client helper.** Run `scripts/api-smoke.py` with a small known file before automating larger workloads.
6. **Parse by endpoint.** `/api` wraps data in `{code, msg, data}`. `/v1/audio/transcriptions` has OpenAI-like text behavior and returns plain text for SRT.

## References

- [references/web-ui.md](references/web-ui.md) describes upload, progress, result display, batch handling, and export controls.
- [references/api-reference.md](references/api-reference.md) lists request fields, response shapes, and client examples for both endpoints.
- [references/troubleshooting.md](references/troubleshooting.md) covers upload, payload, response-format, and client integration failures.
- [../../references/troubleshooting.md](../../references/troubleshooting.md) routes cross-cutting model, ffmpeg, and backend symptoms.

## Helper script

`scripts/api-smoke.py` is an argument-driven replacement for the hard-coded API example. Use it like:

```bash
python scripts/api-smoke.py \
  --endpoint legacy \
  --file sample.wav \
  --model tiny \
  --language en \
  --response-format json
```

Switch `--endpoint openai` to probe the OpenAI-compatible path.

## Response-shape reminders

- Legacy `/api` always returns a JSON envelope. A successful call has `code: 0`, `msg: ok`, and `data` containing the chosen format.
- OpenAI-compatible `text` returns JSON with a `text` field.
- OpenAI-compatible `json` returns a JSON list of timestamp records.
- OpenAI-compatible `srt` returns a `text/plain` response body.

## Troubleshooting priorities

- If conversion fails, go back to setup and verify ffmpeg/ffprobe.
- If request fields are accepted but result is empty, check that the audio contains speech, the model/language fit the input, and the selected output parser matches the endpoint.
- If a browser workflow works but API automation fails, compare field names and endpoint-specific response wrapping in `references/api-reference.md`.
