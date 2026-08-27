# Troubleshooting Guide

This guide covers the integration layer only: QGIS plugin setup, managed dependency installs, MCP config, and agent/provider routing.
For underlying model or geospatial workflow failures, route to the matching sibling sub-skill.

## Quick triage

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| QGIS plugin panel never appears | Plugin not enabled, stale cache, or QGIS restart needed | Open the plugin manager, enable GeoAI, restart QGIS, then check the toolbar and menu again. |
| Installer says dependencies are missing every time | Managed venv is broken or stale | Close QGIS, inspect the cache location, then reinstall through the plugin UI or a clean Pixi environment. |
| `No module named 'strands'` when importing `geoai.agents` | Missing optional agents extra | Install the GeoAI package with its agents extra or an environment bundle that includes Strands. |
| CUDA install fails in the plugin installer | Driver too old, wheel index mismatch, or network/proxy failure | Use diagnostics first, then run the dependency probe and fall back to Pixi or CPU mode if needed. |
| QGIS or Python import crashes on Windows | QGIS embedded Python and the managed venv are fighting over native DLLs | Keep model work in the plugin-managed subprocesses; do not force torch into the QGIS process. |
| Claude Desktop cannot start the MCP server | Bad command, cwd, env, or sandbox path | Validate the JSON and paths with `mcp_config_check.py`. |

## QGIS plugin issues

### 1. Python and PyQt process mismatch

GeoAI model work in the QGIS plugin runs in the managed venv process, not directly in the QGIS embedded Python process.
This avoids the common Windows DLL conflict between QGIS, PyQt, and torch-based libraries.

If you see import errors, missing DLLs, or odd crashes:

- do not `pip install` into the QGIS Python process
- use the plugin installer or Pixi-managed environment instead
- prefer the diagnostics report before changing anything

### 2. Managed cache and venv problems

The installer uses a managed cache directory selected from:

- `GEOAI_CACHE_DIR`
- `GEOAI_VENV_DIR`
- the default home-directory cache under `~/.qgis_geoai/`

If installation fails because the cache location is unwritable or stale:

1. Close QGIS.
2. Pick a writable cache location.
3. Set `GEOAI_CACHE_DIR` before launching QGIS.
4. Re-run the installer.

Do not delete the cache while QGIS is still running.

### 3. CUDA, MPS, and device choice

- On NVIDIA systems, the installer tries to choose the correct CUDA wheel index.
- If the driver is too old for the chosen index, it falls back to CPU.
- On Apple Silicon, MPS can still be available at runtime even when CUDA is irrelevant.
- If CUDA setup keeps failing, use Pixi so the QGIS, PyTorch, and CUDA versions are pinned together.

The most common CUDA failure modes are:

- no `nvidia-smi`
- driver too old for `cu124`, `cu126`, or `cu128`
- corporate proxy blocking wheel downloads
- the user is in a CPU-only or MPS-only environment

### 4. Windows QGIS version pin

If you are on Windows and the plugin stack hits a `.qgz` save failure or a zip error, check the QGIS version first.
Use QGIS 3.44.* for the Pixi route.
Older 3.42.2 Windows builds had a save bug that is unrelated to GeoAI itself.

### 5. Proxy and download failures

If the installer cannot download Python, uv, or dependencies:

- check QGIS proxy settings
- retry after fixing the proxy or certificate chain
- use the dependency probe to confirm the dependency plan before reinstalling

## MCP server issues

### 1. Claude Desktop config validation

Use `mcp_config_check.py` before starting the server if the client cannot connect.
It checks:

- the server command
- the working directory
- the sandbox directories
- the core environment variables
- the timeout and device settings

For sandboxed setups, ensure the input and output directories are absolute, writable, and dedicated to the server.

### 2. Sandbox path failures

The MCP server only allows file access inside the configured input and output directories.
If a tool fails with a path denial:

- check for `..` in the requested path
- check that the path is inside the sandbox
- check that the client did not rewrite the working directory unexpectedly

### 3. Timeout, memory, and device settings

If a server tool times out or runs out of memory:

- increase `GEOAI_TIMEOUT`
- lower the input size or tile size in the request
- set `GEOAI_DEVICE` explicitly when auto-detection is wrong
- review `GEOAI_MAX_MEMORY_GB` if the config is too small for the task

### 4. Logging and stdout rules

The MCP server uses stdio transport.
Keep logs on stderr or in a log file.
Do not print diagnostics or debug output to stdout, or the client may misread the protocol stream.

## Agent and provider issues

### 1. Missing Strands extras

If importing `geoai.agents` fails with `No module named 'strands'`, the environment is missing the optional agents extras.
Install the agents bundle that includes the Strands packages and the provider extras you need.

### 2. Provider API keys

The constructor helpers look for these secrets when a key is not passed directly:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `MINIMAX_API_KEY`
- AWS credentials for Bedrock

Never print the key values in a debug report.
Only verify that the environment variable names are present and populated.

### 3. MiniMax and vLLM routing

- MiniMax helpers use the OpenAI-compatible `https://api.minimax.io/v1` endpoint.
- vLLM helpers assume a live vLLM server and should not trigger downloads from this skill.
- If a local server is down, fix the server first; do not debug it as a GeoAI package issue.

## Recommended probes

```bash
python scripts/qgis_dependency_probe.py --help
python scripts/qgis_dependency_probe.py --platform win32 --python-version 3.12 --gpu auto
python scripts/mcp_config_check.py --help
python scripts/mcp_config_check.py --config claude_desktop_config.json --server-name geoai --strict
```

## Escalation guidance

If the failure is really about raster/vector processing, download planning, model inference, training, or foundation-model selection, route to the sibling sub-skill that owns that workflow.
This sub-skill only owns integration setup, config validation, and troubleshooting.
