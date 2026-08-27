# Troubleshooting

## API server not reachable

**Symptoms**
- `Connection refused` on 8200
- `/health` fails
- client smoke scripts time out immediately

**Likely causes**
- The API server is not running.
- The request is pointed at the wrong port.
- The model endpoint on 8000 is down.

**Fix**
- Check `GET /health` on 8200 first.
- Make sure the mock or real model server is listening on 8000.
- Confirm the file server URL points at 8100 for downloads.

## vLLM endpoint mismatch

**Symptoms**
- `DeepAnalyzeVLLM.generate()` cannot connect
- API server calls fail before a reply is produced

**Likely causes**
- `DeepAnalyzeVLLM` expects `http://localhost:8000/v1/chat/completions` by default.
- The API server's internal model client also expects `http://localhost:8000/v1`.

**Fix**
- Keep the mock or real vLLM endpoint on 8000 unless you update the configuration everywhere that uses it.
- If you change the model port, update both the client and the server-side model base URL together.

## File ids are ignored

**Symptoms**
- The model does not seem to see the uploaded file.
- The prompt looks correct, but the workspace data summary is empty.

**Likely causes**
- `file_ids` were attached to the wrong message.
- The latest user message does not carry the file ids.
- The file was never uploaded successfully.

**Fix**
- Put `file_ids` on the latest user message.
- Keep the complete history and reuse the same files when the same data is still relevant.
- Verify the upload response before calling chat completions.

## Thread id misuse

**Symptoms**
- `Thread ... not found`
- Follow-up turn starts a new workspace unexpectedly
- The history no longer matches the workspace files

**Likely causes**
- `thread_id` was copied onto every message instead of only the latest user message.
- The thread was already cleaned up.
- A stale thread id was reused after a restart.

**Fix**
- Put `thread_id` only on the newest user message.
- Keep the full conversation history in every turn.
- If the thread was cleaned up, start a fresh conversation.

## Generated files are missing

**Symptoms**
- The chat reply exists, but no artifact URLs appear.
- A client checks the wrong field and thinks generation failed.

**Likely causes**
- The code only checked `message.files` or only checked `generated_files`.
- A streaming client ignored the final chunk.
- The workspace artifact was written, but the client never collected the returned metadata.

**Fix**
- Inspect both `message.files` and top-level `generated_files`.
- For streaming calls, inspect the final chunk as well.
- Remember that the download URL is usually served from 8100 under `workspace/<thread_id>/generated/`.

## Workspace cleanup confusion

**Symptoms**
- A thread disappears unexpectedly.
- A generated file is gone after cleanup.

**Likely causes**
- The thread passed the cleanup timeout.
- Manual cleanup was run too early.
- An active workspace was deleted while it was still in use.

**Fix**
- Use `/v1/admin/threads-stats` to inspect age buckets before cleanup.
- Use `/v1/admin/cleanup-threads` only after the analysis is complete.
- Treat thread workspaces as disposable once the conversation is finished.

## Code execution timeout

**Symptoms**
- The API response contains `[Timeout]`.
- A long-running notebook-style task never finishes.

**Likely causes**
- The code exceeded the subprocess timeout.
- A plotting or data-processing step is too large for one round.

**Fix**
- Split the work into smaller code blocks.
- Keep expensive operations out of a single turn.
- Remember that the API server uses a subprocess timeout, while `DeepAnalyzeVLLM.execute_code()` is in-process and has no timeout.

## Matplotlib or CJK font issues

**Symptoms**
- Charts render with missing glyphs.
- Minus signs or Chinese labels look wrong.

**Likely causes**
- A CJK font is missing.
- The non-interactive backend is not configured.

**Fix**
- Use the API runtime's Agg backend behavior for headless execution.
- Set `axes.unicode_minus = False` when needed.
- Install a CJK font if you need Chinese labels in plots.

## Missing dependencies

**Symptoms**
- Import errors for client, API, or analytics helpers.

**Likely causes**
- `requests`, `openai`, `fastapi`, `uvicorn`, or `python-multipart` is absent.
- The analytics examples also need `pandas`, `numpy`, `matplotlib`, `openpyxl`, `seaborn`, or `statsmodels`.

**Fix**
- Install the missing package(s) before retrying the smoke script.
- Keep model-serving extras separate from the CPU smoke path.

## OpenAI client compatibility quirks

**Symptoms**
- A file download or streaming check works in one version of the OpenAI client but not another.

**Likely causes**
- The object layout differs across client versions.

**Fix**
- Guard on `hasattr(message, "files")` and `hasattr(chunk, "generated_files")`.
- When reading file content, tolerate `.text`, `.read()`, or raw bytes.
