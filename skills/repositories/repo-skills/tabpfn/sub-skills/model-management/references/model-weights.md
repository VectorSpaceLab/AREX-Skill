# Model Access, Cache, and Download Behavior

## Access flow

1. TabPFN checks for a cached token.
2. If needed, it opens the browser-based license flow.
3. If browser login is disabled, it falls back to `TABPFN_TOKEN`.
4. Once access is granted, the token is cached locally for reuse.

## Important environment variables

- `TABPFN_TOKEN` — explicit API token for headless or CI environments.
- `TABPFN_NO_BROWSER` — disables browser login and forces token-based access.
- `TABPFN_MODEL_CACHE_DIR` — overrides the model checkpoint cache directory.
- `TABPFN_MODEL_CACHE_SIZE` — enables the built-model LRU cache when positive.

## Cache helpers

- `get_cache_dir()` chooses the platform-appropriate cache root.
- `prepend_cache_path()` resolves filenames into the cache directory.
- `clear_built_model_cache()` clears the opt-in built-model cache.

## Gated vs direct download behavior

- `v2` supports a direct-download fallback.
- `v2.5`, `v2.6`, and `v3` require license acceptance and model-card access.
- Missing or stale access should be treated as a model-management issue, not a prediction issue.

## Offline use

If the user wants offline inference, prepare the cache first and then point the
skill at the local checkpoint path. Do not assume a cache exists just because
`import tabpfn` succeeds.
