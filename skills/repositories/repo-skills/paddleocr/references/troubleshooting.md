# Cross-Cutting Troubleshooting

Use this reference for install/import issues, optional dependency gaps, model download problems, auth failures, and output handling problems shared across PaddleOCR workflows.

## Import and installation failures

### Symptom
- `ModuleNotFoundError: No module named 'paddleocr'`
- `ImportError` or `DependencyError` during predictor or pipeline creation

### Likely causes
- Base package not installed in the active environment.
- A workflow-specific extra such as `doc-parser` or `doc2md` is missing.
- The selected pipeline needs a PaddlePaddle / inference-engine backend that is not installed.

### Recovery
1. Install the base package first.
2. Add only the extra required by the selected workflow.
3. Re-run the bundled smoke helper and the targeted sub-skill script.

## Model download and cache issues

### Symptom
- The first model run is slow, hangs, or fails to download weights.
- A workflow cannot find a model after install.

### Likely causes
- The default model source is unreachable from the current environment.
- The selected model requires a cache or backend that has not been prepared.

### Recovery
- Set `PADDLE_PDX_MODEL_SOURCE=BOS` when HuggingFace access is blocked.
- Re-run the selected workflow only after the cache or model source is available.
- Prefer the sub-skill script or a safe smoke check before attempting a large native test.

## CLI and API misuse

### Symptom
- `paddleocr` exits with usage text or `argparse` errors.
- The hosted API client rejects the request shape or model choice.
- `doc2md` says the format is unsupported.

### Likely causes
- Missing required CLI arguments such as `--input`, `--model_type`, or `--file_path`/`--file_url`.
- Wrong model family chosen for the selected task.
- Invalid option payloads such as unsupported backend flags or bad numeric ranges.

### Recovery
- Start from the relevant sub-skill reference and match the exact command family.
- Check the public option dataclass or CLI flag names in the bundled reference before retrying.
- For `doc2md`, verify the source file extension is one of the supported office formats.

## Hosted API and integration failures

### Symptom
- `AuthError`, `RateLimitError`, `PollTimeoutError`, or `ServiceUnavailableError` from the hosted API client.
- MCP or LangChain integration cannot connect.

### Likely causes
- Missing or invalid `PADDLEOCR_ACCESS_TOKEN`.
- Wrong base URL.
- Unsupported provider/model combination.
- Remote service timeout or rate limit.

### Recovery
- Confirm token and base URL values before retrying.
- Check the integration sub-skill for provider-specific env vars and model restrictions.
- Use fake/mocked unit tests first before attempting a real remote call.

## Output and resource-saving issues

### Symptom
- Results print but resources are missing on disk.
- Saved files are overwritten or filenames look unexpected.

### Likely causes
- The output directory is not writable.
- The workflow expects a results-specific resource saver instead of a generic file copy.
- The document parsing result contains image keys that fail validation.

### Recovery
- Use the workflow-specific helper or the API client's resource-saving methods.
- Verify destination paths and overwrite flags.
- For document parsing resources, preserve the generated relative filenames and do not mutate keys manually.

## Backend mismatch

### Symptom
- A CPU-only environment is being used for a workflow that expects accelerator evidence.
- A GPU/VLM/deployment claim is referenced but not actually verified.

### Recovery
- Treat CPU import/help checks as sufficient only for the base package surface.
- If a later task needs GPU or service evidence, refresh the backend plan and prepare the right environment before claiming success.
