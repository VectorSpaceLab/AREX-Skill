# Headroom SDK troubleshooting

## `import headroom` works but `compress()` or image/relevance helpers fail

Symptoms:
- The package imports, but a helper raises `ImportError`, `RuntimeError`, or complains about a missing model/runtime.

Likely causes:
- Optional extras such as `proxy`, `code`, `relevance`, `image`, `spreadsheet`, or `otel` are not installed.
- A cold cache still needs local model/runtime assets.
- The helper depends on the running proxy rather than the local Python API.

Recovery:
1. Confirm whether the user wants Python local compression or proxy-backed TypeScript/app integration.
2. Check the helper-specific extra in the runtime guidance.
3. For a no-network smoke, use `scripts/compress_smoke.py` or `scripts/tabular_compression_demo.py` first.

## `compress()` returns but no tokens are saved

Symptoms:
- `CompressResult` is returned, but `tokens_saved` is `0` or no transform appears.

Likely causes:
- `optimize=False` was used.
- The message set is too small to trigger compression.
- The chosen config preserves too much recent context or system content.

Recovery:
- Lower `min_tokens_to_compress` and `protect_recent` for the test case.
- Use a larger sample with more repeated or structured content.
- Verify that `CompressConfig` overrides were actually passed in.

## `SharedContext` seems to lose entries

Symptoms:
- A key appears missing after a short delay.
- A stored entry comes back compressed or empty.

Likely causes:
- TTL expired.
- `max_entries` evicted the oldest item.
- The caller is reading the compressed view rather than `full=True`.

Recovery:
- Inspect `ttl` and `max_entries` first.
- Use `get(key, full=True)` when the original content is required.
- Store short-lived experiments in a temporary context object.

## Relevance scoring falls back or raises

Symptoms:
- `create_scorer('embedding')` raises an availability error.
- Hybrid scoring is slower or more limited than expected.

Likely causes:
- `sentence-transformers` is missing.
- The optional embedding cache or model assets are unavailable.

Recovery:
- Use `create_scorer('bm25')` when you only need a zero-dependency fallback.
- Install the relevance extra when semantic matching is actually required.
- Treat hybrid fallback as intentional, not as a bug, when the embedding dependency is absent.

## Image compression or OCR fails

Symptoms:
- `headroom.image` imports, but OCR/model routing fails at runtime.
- The script complains about missing OCR backend or model assets.

Likely causes:
- `image` extra not installed.
- ONNX or OCR runtime assets are absent or unavailable in the current environment.
- A cold cache triggered a download you did not intend to allow.

Recovery:
- Use the bundled safe no-network smoke only to verify imports and basic routing.
- Install the image extra only when the user explicitly wants OCR/image compression.
- Do not claim image support unless the optional dependencies and assets are available.

## TypeScript SDK troubles

Symptoms:
- `headroom-ai` examples compile but fail at runtime.
- The client cannot reach the proxy.

Likely causes:
- No running proxy or wrong base URL.
- Node/npm dependencies are missing.
- A wrapper example expects a local loopback proxy but only a cloud URL is configured.

Recovery:
- Check the proxy with `proxy-wrap` first.
- Use the TS examples as recipes, not as a substitute for a live proxy.
- Confirm the app is using the `headroom-ai` client and not a direct provider client.

## Spreadsheet helper errors

Symptoms:
- `.xlsx` or `.xls` compression fails or returns empty results.

Likely causes:
- The `spreadsheet` extra is missing.
- The input file is not a supported workbook.
- The file is too small to compress meaningfully.

Recovery:
- Use `scripts/tabular_compression_demo.py` to verify the end-to-end helper path.
- Check file extension and workbook validity.
- Report unsupported formats separately from compression quality issues.
