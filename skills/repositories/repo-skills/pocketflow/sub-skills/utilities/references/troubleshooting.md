# Utilities troubleshooting

## Missing API keys

### Symptoms
- Provider helpers fail immediately.
- Error messages mention an unset environment variable.

### Fix
- Document the key name clearly.
- Fail with a readable message before making a network request.
- Keep local validation separate from network smoke checks.

## Provider rate limits

### Symptoms
- Parallel or repeated calls start failing.

### Likely causes
- Too many concurrent requests.
- Retries are too aggressive.

### Fix
- Add throttling or a small sleep.
- Keep retries idempotent.
- Consider sequential execution when the provider is sensitive.

## Malformed wrapper output

### Symptoms
- A node expects text, a list, or a vector but receives a different shape.

### Likely causes
- The wrapper does not normalize the result.
- The provider SDK changed its return type.

### Fix
- Convert provider objects to a stable Python type before returning them.
- Add a local validation check on the output shape.

## Vector dimension mismatch

### Symptoms
- Searching a vector index raises a dimension error.

### Likely causes
- Indexing and query embeddings come from different models.
- The wrapper does not enforce a fixed embedding size.

### Fix
- Validate the vector length before storing or querying.
- Use the same embedding family for both indexing and retrieval.

## Chunking mistakes

### Symptoms
- Chunks are too large or split awkwardly.
- Empty input crashes the helper.

### Fix
- Make the chunk size explicit.
- Return an empty list for empty text.
- Prefer a simple first-pass chunker before adding semantic logic.

## Unsafe SQL or database access

### Symptoms
- The helper interpolates values directly into query strings.

### Fix
- Use parameterized queries.
- Separate query construction from query execution.
- Close connections or use context managers.

## Audio and PortAudio issues

### Symptoms
- Playback or microphone capture fails on Linux/macOS/Windows.

### Likely causes
- The host audio backend is missing.
- The local package is installed without the platform audio dependency.

### Fix
- Document the platform-specific dependency clearly.
- Keep a non-audio fallback path for local testing.

## Tracing credentials or service errors

### Symptoms
- The app crashes when tracing is enabled.

### Likely causes
- Missing tracing keys or host URL.
- The tracing backend is unavailable.

### Fix
- Treat tracing as optional unless the user explicitly needs it.
- Provide a no-tracing mode or a local logging-only path.

## Parallel rate limits

### Symptoms
- A parallel async helper works locally but triggers service errors.

### Fix
- Add a concurrency cap.
- Switch to sequential mode when the external service is the bottleneck.
- Remember that parallel async is for overlap, not unlimited throughput.
