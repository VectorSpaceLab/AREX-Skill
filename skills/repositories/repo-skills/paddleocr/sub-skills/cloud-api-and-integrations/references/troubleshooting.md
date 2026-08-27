# Hosted API, MCP, and LangChain Troubleshooting

## Missing token or base URL

### Symptom
- `AuthError` from `PaddleOCRClient`
- MCP validation says the access token or base URL is required

### Likely causes
- `PADDLEOCR_ACCESS_TOKEN` is unset.
- A provider-specific base URL is missing.

### Recovery
- Set the required env var before retrying.
- Use the bundled setup checker to validate configuration without sending a request.

## Model or task mismatch

### Symptom
- The CLI rejects the selected model for the requested task.
- The client raises `InvalidRequestError` before a request is sent.

### Likely causes
- An OCR model was selected for a document-parsing request or vice versa.
- A provider only supports a subset of the model families.

### Recovery
- Check the official-api reference for the allowed model families.
- Keep OCR and document-parsing requests separate.

## HTTP, polling, or service failures

### Symptom
- `RequestTimeoutError`
- `PollTimeoutError`
- `RateLimitError`
- `ServiceUnavailableError`
- generic `APIError`

### Likely causes
- The remote service is slow, unavailable, or rate-limited.
- The request timeout or poll timeout is too short.

### Recovery
- Retry with a longer timeout only after confirming the request shape.
- Distinguish server-side failure from network failure using the error class.

## Resource saving problems

### Symptom
- Saved resources are missing or malformed.
- The document-parsing resource save helper rejects a filename key.

### Likely causes
- The destination path is not writable.
- The result contains an unsafe resource key that fails validation.

### Recovery
- Use the client resource helpers instead of reconstructing filenames manually.
- Preserve the generated relative filenames and keep the destination directory writable.

## MCP provider issues

### Symptom
- The MCP server exits with a provider or validation error.
- A host config works for one provider but not another.

### Likely causes
- The selected provider needs a different token or base URL.
- `--http` was omitted while trying to use host/port flags.
- The model selection violates the provider's model restrictions.

### Recovery
- Read the provider table before changing the command line.
- Keep local, AI Studio, Qianfan, and self-hosted modes separate.

## LangChain loader issues

### Symptom
- `PaddleOCRVLLoader` fails to load a file or URL.
- The loader returns no text.

### Likely causes
- The file path does not exist.
- The hosted API could not parse the file.

### Recovery
- Confirm the source path or URL first.
- Inspect the raw response metadata on the returned `Document` objects to see what the service produced.
