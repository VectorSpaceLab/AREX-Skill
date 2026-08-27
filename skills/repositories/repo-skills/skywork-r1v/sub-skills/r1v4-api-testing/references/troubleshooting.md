# Troubleshooting

## Quick symptom map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing API key or base URL | The caller did not provide an env var or config value. | Set the key in env or caller config, then rebuild the payload preview. Do not hard-code the key into runtime files. |
| `401` / `403` | Invalid bearer token, wrong account, or wrong service base URL. | Re-check the `Authorization: Bearer ...` header source and the API host before retrying. |
| `429` | Rate limiting or too many concurrent requests. | Lower concurrency, add backoff, and retry later. |
| `5xx` | Service-side failure or a transient upstream problem. | Retry with the same dry-run payload; if the error persists, reduce payload size or wait and retry. |
| Timeout | The request or stream took longer than the chosen timeout. | Increase the timeout in the caller, simplify the prompt, or test with one case first. |
| MIME type unknown | `mimetypes.guess_type()` could not infer a type for the image file. | Pass an explicit MIME type to the payload builder, convert the file to a common image type, or provide an already-encoded data URL. |
| Bad image path | The image path is not valid relative to the case file or current directory. | Run `validate_cases.py --check-images` and fix the relative path or move the image. |
| SSE parse failure | The stream response does not match the expected `data:` format or the parser ignored a chunk. | Confirm the service is returning SSE lines, then inspect `response.raw_events` and re-run the parser. |
| Malformed `<tool_call>` or `<observation>` JSON | The response tags are present but the JSON inside the tag is invalid. | Use `parse_r1v4_response.py` to preserve the raw text and review the parse-error field before attempting downstream automation. |
| Result schema mismatch | The JSONL record does not contain `response.full_response` or uses a different top-level layout. | Normalize the file with the parser, or update the downstream consumer to read the actual record shape. |
| Viewer path or image display problems | The interactive viewer depends on local file paths and browser access. | Prefer `summarize_results.py` for headless checks, and make sure the image path still exists if you need visual inspection. |
| Unexpected effect from `enable_search` | Search can change latency, tool use, and answer style. | Keep `enable_search` false for the regular batch scripts unless you intentionally want search behavior. |

## Recovery checklists

### API access failures

1. Confirm the API host is `https://api.skyworkmodel.ai` unless your caller config overrides it.
2. Confirm the endpoint is `/api/v1/chat/completions`.
3. Confirm the request uses a bearer token from env or caller config.
4. Rebuild the payload preview before attempting another live call.

### Image ingestion failures

1. Validate the `test_cases.jsonl` file with `validate_cases.py`.
2. Resolve each image path relative to the case file and current directory.
3. Confirm the file extension matches the file contents or supply an explicit MIME type.
4. If the case is text-only, leave `image` empty instead of inventing a placeholder path.

### Stream parsing failures

1. Check whether the stream output contains `data:` lines and a final `[DONE]` marker.
2. Compare the raw SSE lines against `response.raw_events`.
3. Re-run `parse_r1v4_response.py` on the concatenated content, not on the raw event stream.

### Tag and JSON parsing failures

1. Keep the raw response intact.
2. Inspect the raw `<think>`, `<tool_call>`, `<observation>`, and `<answer>` blocks.
3. Use the parser output to separate malformed JSON from malformed tagging.
4. Fix the upstream generator only after you know which tag failed.

### Viewer problems

1. Confirm that the result JSONL file itself loads.
2. Confirm that the image path exists where the viewer expects it.
3. Use the summary helper if you only need counts.
4. Avoid depending on browser state for batch automation.
