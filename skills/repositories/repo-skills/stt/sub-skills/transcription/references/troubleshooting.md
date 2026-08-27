# Transcription troubleshooting

## Upload errors in the browser

Symptoms:

- Upload fails before recognition starts.
- File preview never appears.
- Browser shows an unsupported file-type alert.

Check:

1. The file extension is one of the supported audio/video extensions.
2. ffmpeg and ffprobe are available; route back to setup if conversion fails.
3. The file is readable and not still being written by another program.

## `.en` model with non-English language

The browser checks model names ending in `.en` and alerts when the selected language is not English. Use an English language code, choose a multilingual model, or set language detection to automatic when the audio language is uncertain.

## API request says file is missing

For both public API paths, the file must be uploaded as multipart field `file`. Do not send only a local path string in JSON, and do not rename the part to `audio` or any other field name.

If the request still fails, compare it with [scripts/api-smoke.py](../scripts/api-smoke.py) to verify the multipart shape and endpoint choice.

## Legacy API returns non-zero `code`

A non-zero `code` means the server caught an application-level error. Common causes:

- ffmpeg conversion failed;
- model load failed or model download was unavailable;
- input file path in temporary storage is missing;
- transcription raised a backend error.

Inspect `msg` and then route to setup troubleshooting if the cause is model/backend/conversion.

## OpenAI-compatible response is hard to parse

Match parser to `response_format`:

- `text` returns JSON with a `text` field.
- `json` returns a JSON list.
- `srt` returns a plain text body.

If an OpenAI SDK wrapper expects a different response shape, first validate with raw HTTP or [scripts/api-smoke.py](../scripts/api-smoke.py).

## OpenAI client wiring looks wrong

If a client call fails before transcription starts, check the base URL and endpoint path:

- raw HTTP helpers should target the server root and append the route path themselves;
- OpenAI-style clients should use the `/v1` base URL that the SDK expects;
- do not append `/v1` twice.

## Empty or near-empty output

Likely causes:

- audio contains silence, music, or non-speech;
- selected language does not match speech;
- `.en` model is used for non-English speech;
- VAD filters speech too aggressively;
- input is too noisy or low volume;
- output parser is looking at the wrong field.

Try a shorter clear speech sample, set language explicitly, switch model, and compare `text` versus `json` format to see whether segments were filtered.

## Batch export confusion

- Auto export downloads each result as it finishes when enabled.
- Individual export controls whether manual export downloads per-file outputs or one combined text file.
- Manual export stays disabled until at least one result exists.

## Slow progress

Progress is based on segment timestamps over total audio duration. Large models, long media, CUDA memory pressure, or first-use model download can delay visible progress. Confirm the server process is still running before resubmitting the same batch.
