# Headroom proxy and wrap troubleshooting

## Proxy starts but traffic still bypasses it

Symptoms:
- `headroom proxy` is running, but the provider still shows direct traffic.
- Savings remain at zero even though the app appears configured.

Likely causes:
- The client is pointed at the wrong base URL or wrong route path.
- Claude Code is in Bedrock mode and bypasses `ANTHROPIC_BASE_URL`.
- The wrapper is not the active launcher in the shell or editor session.
- A durable config file is stale and was not refreshed.

Recovery:
1. Confirm the live proxy URL with `python scripts/proxy_livez_check.py --url http://127.0.0.1:8787`.
2. Re-check the wrapper command in the same shell.
3. For Claude, ensure normal Anthropic mode when routing through the proxy.
4. For editor integrations, inspect the provider/base URL settings the wrapper wrote and remove stale duplicates.

## `headroom wrap` cannot find the target agent

Symptoms:
- The wrapper says the agent is missing or unsupported.
- A launcher exists but the wrapper cannot detect it.

Likely causes:
- PATH does not include the expected binary.
- The agent uses a local npm bin, global npm bin, or Python fallback that the wrapper did not discover.
- The target is not one of the supported agent names.

Recovery:
- Check the supported names in `headroom wrap --help`.
- Verify launcher discovery with `command -v <agent>` or the agent's own install instructions.
- For OpenClaw/OpenCode, ensure the appropriate plugin or provider package is installed before expecting the wrapper to succeed.

## OpenClaw or OpenCode plugin errors

Symptoms:
- The plugin installs but the agent still does not route through Headroom.
- The plugin complains about no local proxy or wrong launch order.

Likely causes:
- The wrapper expected a local proxy but the user only configured a remote URL.
- Local npm bin, global npm bin, or Python fallback detection found an unexpected launcher.
- The current plugin config is stale and contains an old proxy URL.

Recovery:
- Confirm whether the user wants a local auto-start proxy or a connect-only remote proxy.
- Reinstall or refresh the plugin only after confirming the target proxy URL.
- Remove stale provider/baseUrl overrides from the agent's config when needed.

## Bedrock or Vertex issues

Symptoms:
- Proxy launches but provider calls fail with AWS/GCP auth or model-name errors.

Likely causes:
- Missing AWS/GCP credentials or region.
- Bedrock model identifiers or inference profile ARNs are invalid.
- The user is using an agent mode that bypasses the proxy.

Recovery:
- Verify credentials and region first.
- Use the documented model identifier or application inference profile ARN format.
- Test the proxy with a local health check before attempting live cloud traffic.

## TLS, model assets, and import-time failures

Symptoms:
- The proxy or import path fails behind a corporate TLS-inspection network.
- ONNX, Hugging Face, or OCR assets fail to load.
- The process imports but runtime models are unavailable.

Recovery:
- See `ops` troubleshooting for CA and ORT/Hugging Face guidance.
- For proxy-only diagnosis, prefer `/livez` and `/health` before checking model-backed features.
- Do not assume a missing model download means the proxy is down.

## Cache-safety confusion

Symptoms:
- Users expect a passthrough path to mutate bytes.
- Metrics show cache-safety alarms or unexpected compression changes.

Recovery:
- Distinguish a compression path from a passthrough path.
- If the user asked for exact byte preservation, ensure the selected route is not a compression route.
- Check proxy metrics and the route-specific debug output before changing config.
