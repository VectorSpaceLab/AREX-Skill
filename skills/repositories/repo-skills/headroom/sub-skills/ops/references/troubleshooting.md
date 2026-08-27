# Headroom ops troubleshooting

## `headroom` command not found

Symptoms:
- Shell says `headroom: command not found`.
- MCP clients cannot spawn `headroom mcp serve`.

Likely causes:
- Installed the TypeScript package only; npm `headroom-ai` is a library and does not provide the Python CLI.
- `uv tool` or `pipx` binary directory is not on `PATH`.
- The agent process starts with a non-interactive `PATH`.

Recovery:
1. Install the Python package with `uv tool install "headroom-ai[all]"` or `pip install "headroom-ai[proxy]"`.
2. Run `command -v headroom` in the same shell or service environment.
3. For MCP clients that do not inherit `PATH`, configure the absolute executable path returned by `command -v headroom`.

## `headroom doctor` reports proxy down

Symptoms:
- `doctor` exits 2.
- Dashboard/stats are unreachable.

Recovery:
- For foreground use, route to `proxy-wrap` and run `headroom proxy --port 8787`.
- For persistent deployments, run:

  ```bash
  headroom install status --profile default
  headroom install start --profile default
  ```

- If a different service owns the port, choose another port and update wrapping/deployment config.

## Version drift

Symptoms:
- `doctor` warns proxy version differs from installed package.
- You updated Headroom but savings behavior still looks old.

Recovery:
- Restart the running proxy or persistent profile.
- If installed from a source checkout/editable install, use git/build workflow; `headroom update` may refuse to self-update.
- If a Windows native extension is locked, stop the proxy before updating.

## `headroom update` refuses

Common valid refusals:
- Externally managed system Python (PEP 668).
- Editable/source checkout.
- Docker image runtime.
- Unsupported package manager or locked native library.

Recovery:
- Use `pipx`, `uv tool`, or a virtual environment rather than forcing pip into a managed system Python.
- For Docker, pull and redeploy the image.
- For git checkouts, use `git pull` and reinstall/build as needed.

## Savings/perf reports are empty

Symptoms:
- `headroom savings` says no savings recorded.
- `headroom perf` reports no PERF records.

Likely causes:
- No traffic has passed through the proxy.
- The app/agent is not routed through Headroom.
- Logs or savings state were redirected with `HEADROOM_WORKSPACE_DIR` or per-resource path variables.
- Proxy is running in stateless mode.

Recovery:
1. Run `headroom doctor`.
2. Check routing under `proxy-wrap`.
3. Inspect canonical paths with `python scripts/diagnose_headroom_install.py --json`.
4. Send a small routed request, then re-run reports.

## `inspect` cannot diff messages

Symptoms:
- `headroom inspect` says the proxy is not capturing message content.

Recovery:
- Restart the proxy with message logging only if the user accepts local storage of message snapshots.
- Use `perf` and `savings` for aggregate reports when content logging is not acceptable.

## Corporate TLS or model-asset failures

Symptoms:
- `CERTIFICATE_VERIFY_FAILED` during install or model download.
- ONNX/Hugging Face assets fail behind corporate SSL inspection.
- Python 3.13 strict CA errors mention `Basic Constraints`.

Recovery:
- Install Rust first only when building from source is required and the build backend would otherwise download it.
- Use `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, or `CURL_CA_BUNDLE` for trusted corporate roots.
- For strict CA failures that Headroom controls, `HEADROOM_TLS_STRICT=0` relaxes only OpenSSL's strict CA-constraint flag while preserving hostname/signature validation.
- For ONNX Runtime asset issues, pre-provision ORT and use `ORT_STRATEGY=system`, `ORT_LIB_LOCATION`, or runtime `ORT_DYLIB_PATH` as documented by the install guide.

## Bundled tools missing or unsupported

Symptoms:
- `headroom sg`, `headroom diff`, or `headroom loc` fails.
- `headroom tools doctor` reports `missing` or `unsupported-platform`.

Recovery:
- Run `headroom tools list` to see supported platforms.
- Run `headroom tools install` only if downloads are allowed.
- If a platform is unsupported, use the system package for the underlying tool or avoid the helper.

## Evals fail

Separate these classes before debugging Headroom itself:

- Missing LLM API key or model access.
- Dataset/download/network unavailable.
- Budget/parallelism too high.
- Optional package extra not installed.
- Real assertion failure in compression, retention, or memory behavior.

Start with a small sample (`-n 1`, low parallelism) and capture JSON output when available.
