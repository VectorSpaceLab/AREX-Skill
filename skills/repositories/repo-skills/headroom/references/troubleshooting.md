# Cross-cutting Headroom troubleshooting

## Import and native extension

- If `import headroom` fails, verify the distribution name (`headroom-ai`) and Python version, then run `python -m pip check`.
- If `_core` import fails, distinguish a broken wheel/build from an optional ONNX/model-runtime failure. Run `python -c "import headroom._core"` before starting a proxy.
- Source/editable installs compile a Rust/PyO3 extension; release wheels avoid a local Rust build when a matching wheel exists.

## Missing extras

- Base import does not prove `proxy`, `memory`, `code`, `image`, `relevance`, `spreadsheet`, or `otel` are installed.
- Install only the extra owned by the failing workflow. Prefer BM25 when embedding relevance is optional, local SQLite when service-backed memory is unnecessary, and CPU image/OCR paths before accelerator-specific options.

## CLI vs npm package confusion

- `pip install headroom-ai[...]` provides the Python package and `headroom` CLI.
- `npm install headroom-ai` provides the TypeScript SDK and no `headroom` CLI.

## No savings

- A healthy proxy can still be unused. Run `headroom doctor`, check `ANTHROPIC_BASE_URL`/`OPENAI_BASE_URL`, and inspect savings/perf logs.
- Small messages, protected recent turns, `optimize=False`, passthrough mode, or a disabled Kompress path can legitimately produce zero savings.

## Paths and stale state

- State is normally under `~/.headroom`; config is under `~/.headroom/config`.
- `HEADROOM_WORKSPACE_DIR` and per-resource overrides can make reports look empty if the CLI and proxy use different roots.
- Use `headroom.paths` or the ops diagnostic helper rather than guessing project-local database/log locations.

## TLS and model assets

- Corporate SSL inspection can break PyPI/model downloads even when loopback proxy health is fine.
- Set a trusted CA bundle for network clients. `HEADROOM_TLS_STRICT=0` is a narrow fallback for Python 3.13+ strict CA constraints; it is not a general certificate-verification disable.
- For ONNX/Hugging Face failures, prefer pre-provisioned assets or offline mode and keep the proxy's local health path separate from model readiness.

## Config mutation and credentials

- Do not overwrite malformed user JSON/TOML config. Fix or move it after taking a backup, then rerun `init`, `wrap`, or `mcp install`.
- Do not run credentialed Bedrock/Vertex/Strands examples as installation tests.
- Do not expose tokens in generated scripts, logs, or reports.
