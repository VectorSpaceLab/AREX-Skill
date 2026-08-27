# Cross-Cutting Troubleshooting

## `quip-miner` command not found

1. Confirm the active Python environment has the package installed:

   ```bash
   python -c "import quip_cli; from importlib.metadata import version; print(version('quip-protocol'))"
   ```

2. If `quip_cli` imports but `quip-miner` is missing, the console-script entry point was not installed; reinstall the package in the active environment.
3. If working from a checkout, use `python -m pip install -e .` or the backend-specific editable install.

## Optional backend import failures

- Missing `cupy`: install the CUDA extra and verify the driver with `nvidia-smi` plus the CuPy allocation smoke in `references/installation-and-environment.md`.
- Missing `pyobjc`/Metal: use a macOS Apple Silicon environment and install the `metal` extra.
- Modal unavailable: install/authenticate Modal before running live Modal jobs; config/CLI guidance can still be used without cloud auth.
- D-Wave credentials missing: set provider credentials in the environment, never in TOML. Do not read or print `.env` files.

## Validator or chain problems

Common operator-facing errors:

- `validators-unreachable`: every configured validator URL failed to connect. Check URL scheme (`ws://` or `wss://`), firewall, validator process, and failover list order.
- `wallet-underfunded`: the signer account balance is below the registration threshold and no suitable faucet/top-up path was available.
- `NoRegisteredTopology` or topology mismatch: the chain lacks a registered topology or local assumptions do not match the chain snapshot. Bootstrap only dev chains with `--seed-chain`; production topology is chain-governed.
- Syncing validator: telemetry may show `sync_state`; wait for sync or switch validators.

## Config file errors

- `[miner] mempool = ...` is invalid. Move `mempool` into the owning backend section.
- A quoted TOML boolean like `mempool = "false"` is invalid; use unquoted `false`.
- Do not pass `--num-cpus`, `--gpu-backend`, `--qpu-type`, or `--daily-budget` to override a backend group already declared in TOML; that is a config conflict by design.
- Use `python scripts/quip_config_lint.py --config config.toml --json` to inspect parsed miner/backend sections, selected modes, mempool owner, and submission settings.

## Telemetry is stale or partially unavailable

- `/health` only proves the telemetry HTTP process is alive.
- `/api/v1/stats` returns 503 while a miner child is still starting or if no fresh snapshot exists.
- Chain-backed endpoints can return 502/503 even when snapshot endpoints work; the telemetry process owns its own validator client.
- In multi-backend containers, one telemetry aggregator reads per-mode files named `telemetry-stats-*.json` and merges counters/miner lists.

## Secret handling

- Do not open, copy, or display `.env`.
- Do not put API keys, tokens, or private seeds in TOML.
- Hybrid keystore JSON stores a plaintext master seed; keep file permissions tight and back it up securely.
- NodeDescriptor building scrubs secret-looking fields, but operators should still keep credentials out of config values.

## Live QPU/cloud safety

Never run paid QPU sampling, cloud GPU jobs, broad benchmarks, Docker validator live integration, or host-mutating systemd scripts unless the operator explicitly asks for that side effect and budget/runtime.
