# Headroom operator workflows

## Install a user-facing CLI/package

Choose the public install path that matches the user's environment:

```bash
uv tool install --python 3.13 "headroom-ai[all]"
pip install "headroom-ai[all]"
docker pull ghcr.io/chopratejas/headroom:latest
```

Use narrower extras when the user needs less surface:

- `proxy` for local proxy/MCP server dependencies.
- `memory` for local memory stores and memory CLI/API.
- `code` for tree-sitter AST-aware code compression.
- `relevance` for embedding relevance scoring.
- `image` for image/OCR compression.
- `spreadsheet`, `html`, `reports`, and `otel` for those workflow families.

Avoid `all` in constrained CI or locked-down systems when only a CLI diagnosis is needed.

## Deploy a persistent local proxy

For a guided deployment:

```bash
headroom deploy --profile default --port 8787 --backend anthropic
headroom install status --profile default
```

For explicit control:

```bash
headroom install apply \
  --profile default \
  --preset persistent-service \
  --runtime python \
  --port 8787 \
  --backend anthropic \
  --providers auto
```

Use `--memory` only when persistent memory injection should run in the proxy. Use `--env KEY=VALUE` for supervised runtimes because systemd/launchd/cron profiles do not inherit the interactive shell environment.

## Diagnose a silent no-savings setup

1. Run the broad checker:

   ```bash
   headroom doctor
   ```

2. If the proxy is down, route to `proxy-wrap` for `headroom proxy` or to this sub-skill for persistent `headroom install start`.
3. If the proxy version differs from installed Headroom, restart the persistent profile or running proxy.
4. If the agent is not routed, route to `proxy-wrap` for durable `wrap` repair.
5. If savings are zero but traffic is routed, inspect mode and logs:

   ```bash
   headroom perf --hours 24
   headroom savings
   headroom inspect --last 3 --full
   ```

`inspect` requires the proxy to have message content logging enabled. If it reports no transformations feed, restart the proxy with the documented logging option only when the user accepts local message logging.

## Manage output-token reduction

1. Learn a baseline:

   ```bash
   headroom learn --verbosity
   headroom learn --verbosity --apply
   ```

2. Enable the shaper before starting or wrapping a proxy session:

   ```bash
   export HEADROOM_OUTPUT_SHAPER=1
   headroom proxy --port 8787
   ```

3. Report savings:

   ```bash
   headroom output-savings
   ```

For a measured number instead of a synthetic estimate, set `HEADROOM_OUTPUT_HOLDOUT=0.1` before traffic and explain that 10% of requests are intentionally unshaped.

## Use bundled code-navigation tools

Check tool availability:

```bash
headroom tools doctor
headroom tools list
```

Use pass-through commands exactly like their underlying tools:

```bash
headroom sg run --pattern 'foo($A)' --lang python .
headroom diff old.py new.py
headroom loc .
```

If `tools doctor` reports missing downloaded binaries, `headroom tools install` downloads to Headroom's per-user cache; ask before doing this on air-gapped or audited systems.

## Run evals safely

- Use `headroom evals probes` for offline recorded-data checks.
- Use `headroom evals memory` or `memory-v2` only after confirming LLM API keys, budget, and desired sample size.
- Use `headroom evals adversarial` as a bounded robustness experiment, not as a default smoke.
- Do not treat an eval failure as an install failure until you separate missing API keys, missing datasets, model refusal, and actual compression bugs.
