# JavaScript SDK Troubleshooting

## Common issues

- **Auth conflict**: do not set both access token and API key at the same time.
- **Snake case in JS payloads**: use the JS client options such as `searchMode`, `searchSettings`, `ragGenerationConfig`, and `collectionIds` instead of raw API field names.
- **File upload fails in browser**: use a `File` object; browser file paths are not supported.
- **Stream handling confusion**: `retrieval.rag({ ragGenerationConfig: { stream: true } })` returns a `ReadableStream` that must be read chunk by chunk.
- **Refresh callbacks not firing**: ensure the token callbacks are provided in the constructor options.
- **Server connection issues**: verify the R2R server is reachable and the base URL is correct.

## Recovery steps

1. Run `scripts/js_sdk_quickstart.mjs --help` for the safe CLI surface.
2. Confirm the JS runtime is Node or a browser with the right stream and FormData support.
3. If the issue is ingestion, retrieval, graph, or server setup rather than JS syntax, route to the sibling sub-skill.
