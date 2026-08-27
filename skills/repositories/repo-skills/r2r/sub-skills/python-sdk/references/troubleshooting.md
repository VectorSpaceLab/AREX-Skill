# Python SDK Troubleshooting

## Common issues

- **Both auth paths set**: the client raises `Cannot have both access token and api key.` Use either login-token or API-key auth, not both.
- **`401` or `403`**: confirm the correct auth path, `R2R_API_BASE`, and `x-project-name` if your deployment uses projects.
- **Unexpected wrapper access**: unwrap `R2RResults.results` or `PaginatedR2RResult.results` before reading the typed payload.
- **Pagination confusion**: `results` holds the page items and `total_entries` holds the count.
- **`BytesIO` download confusion**: `documents.download()` returns a file-like object; it is not a path string.
- **Async misuse**: use `await` on async methods and `async with` on `R2RAsyncClient`.

## Recovery steps

1. Confirm the client constructor and auth state.
2. Re-run `scripts/python_sdk_smoke.py` without network to confirm the import surface.
3. If the issue is actually document, retrieval, graph, or server behavior, route to the sibling sub-skill instead of guessing in Python client code.
