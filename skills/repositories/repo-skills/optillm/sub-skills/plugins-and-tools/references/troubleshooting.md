# Plugin Troubleshooting

## Plugin missing from `plugin_approaches`

**Symptoms:** model prefix is treated as part of the model name or `Unknown approach` is raised.

**Causes:** plugin import failed, missing `SLUG`/`run`, custom plugin directory not set, or dependency missing.

**Fix:** Run:

```bash
python scripts/plugin_matrix.py --check-imports
```

Then install missing dependencies or set `OPTILLM_PLUGINS_DIR` / `--plugins-dir` to the directory containing plugin modules.

## MCP import or connection failures

- If import fails on `mcp.client.websocket`, use `mcp<2` for the current repo code or update the plugin imports for MCP 2.x.
- If a stdio server command is not found, ensure the executable is on `PATH` or use an absolute command path in the MCP config.
- If SSE/WebSocket servers fail, verify URL, headers, environment-variable expansion, timeout, and network reachability.
- Tool execution errors may come from the MCP server itself; inspect server-specific logs.

## Memory persistence issues

- Missing file: acceptable first run; memory starts empty.
- Corrupt JSON: plugin degrades to empty memory.
- Wrong JSON shape: ignored rather than trusted.
- Sensitive content: memory files may contain prompt-derived data; store them in a secure location.

## Privacy plugin slow or incomplete

- Presidio/spaCy resources can take time to initialize.
- Entity recognizers may miss domain-specific identifiers.
- Logs before anonymization may still contain raw text depending on deployment.
- If deanonymized output is wrong, inspect the entity map and replacement order.

## JSON plugin downloads a model unexpectedly

The JSON plugin initializes a default HuggingFace model if used without an existing model object/cache. For pure provider-native JSON mode, avoid the plugin and pass `response_format` through direct proxy. For plugin use, pre-cache the intended small model and test a tiny schema first.

## Proxy plugin routes poorly or backs up

- Check provider weights, `fallback_only`, `model_map`, per-provider `max_concurrent`, global queue limits, and request/connect timeouts.
- Use `round_robin` for even traffic, `weighted` for capacity-weighted traffic, and `failover` for primary/backup behavior.
- Health checks can mark slow providers unhealthy; tune interval and timeout.

## Browser/search failures

`web_search` needs a working browser/driver setup and can encounter CAPTCHAs, blocked automation, or corporate proxy restrictions. Prefer explicit web-search approval and keep fallback plans for no-browser environments.

## Code execution risk

`executecode` and `coc` can execute generated or prompt-provided Python. Run only in a sandbox with constrained filesystem/network access. If no sandbox is available, ask the user before enabling and prefer simulation/review instead of execution.

## SPL state surprises

Learning mode can create or refine strategy data. In shared environments, disable `spl_learning` unless strategy persistence is intended and storage paths are controlled.

## LongCePO delimiter errors

If LongCePO returns irrelevant answers or cannot split input, check that the prompt contains exactly the configured context delimiter (default `<CONTEXT_END>`) between context and query.
