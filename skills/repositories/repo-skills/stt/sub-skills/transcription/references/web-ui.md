# Browser UI workflow

## Upload controls

The browser UI accepts file uploads with these extensions: `mp4`, `mp3`, `flac`, `wav`, `aac`, `m4a`, `avi`, `mkv`, `mpeg`, and `mov`. Users can click the upload area or drag files into it. Multiple files are accepted in one batch.

After upload, the app converts each input to mono 16 kHz WAV with ffmpeg and shows a preview list. If conversion fails, treat it as a setup/ffmpeg issue before debugging transcription.

## Form choices

- **Pronunciation language:** choose an explicit language code or automatic detection.
- **Model:** choose from the configured model list. `.en` models should be used only for known-English audio.
- **Return format:** `srt`, `json`, or `text`.
- **Auto export:** when enabled, each result is downloaded automatically after recognition.
- **Exact current labels:** the English template currently shows `Auto Export`, `Individual export`, `Export Text`, and a start button labeled `Start Separate` with the current `devtype` suffix.
- **Individual export:** when enabled, each file exports separately; when disabled, manual export combines all current results into one text file.

## Batch behavior

When the user clicks the start button, the UI submits one process request for each uploaded WAV. Each item polls progress independently and appends a result textarea when done. The UI disables the start button while processing so users do not queue the same batch twice.

The background worker processes tasks from an in-memory queue. Long files, large models, and CUDA memory pressure can make progress look slow even if the server is alive.

## Result display

- `text`: displayed as joined recognized text.
- `json`: displayed as serialized JSON in the result textarea.
- `srt`: displayed as subtitle blocks.

Manual export is enabled only after at least one result exists. If independent export is enabled, each result is downloaded with a matching extension. If independent export is off, the UI combines all result text into one file.

## Internal route flow for debugging

- `/upload`: receives the browser upload, saves it, converts it with ffmpeg, and returns the generated WAV name.
- `/process`: creates a queue entry containing `wav_name`, `model`, `language`, and `data_type`.
- `/progressbar`: reports progress and returns the final `result` when complete.

These routes are implementation details for the browser. For automation, prefer `/api` or `/v1/audio/transcriptions` instead of scripting the internal upload/process/progress sequence.

## Practical guidance

- Use short files and small models for first validation.
- If using CUDA, prove the same file works on CPU before diagnosing GPU-only errors.
- Avoid large-v3 on low-memory machines.
- Keep the browser page open until every queued result finishes or fails.
