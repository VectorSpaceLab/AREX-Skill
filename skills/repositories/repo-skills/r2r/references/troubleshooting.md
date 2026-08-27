# Cross-Cutting Troubleshooting

Use the nearest sub-skill's troubleshooting page first, then return here if the problem spans multiple R2R surfaces.

## Common failure modes

- **Import fails**: confirm `r2r` is installed in a Python 3.10-3.12 environment and re-run `python scripts/check_r2r_environment.py`.
- **Auth conflict**: the Python client refuses to use both an access token and an API key at once. Choose one path and unset the other.
- **Unexpected 401/403**: check `R2R_API_KEY`, login token state, and `x-project-name`.
- **Server startup trouble**: route to `sub-skills/server-configuration/`; `r2r-serve` needs database and provider settings that are not safe to guess.
- **Empty search or bad retrieval output**: route to `sub-skills/retrieval-rag/` and check search mode, filters, and streaming handling.
- **Missing documents or bad filters**: route to `sub-skills/ingestion-documents/` and validate the filter shape.
- **Graph work not appearing**: route to `sub-skills/graph-workflows/` and check extraction/build/pull sequence.
- **JavaScript request shape looks wrong**: route to `sub-skills/javascript-sdk/` and confirm camelCase transformation and stream handling.

## Quick recovery pattern

1. Identify whether the failure is client, ingestion, retrieval, graph, JS, or server-side.
2. Check the owning sub-skill's troubleshooting reference.
3. Use the bundled helper script for that sub-skill before reopening the source repository.
