# Supervisor and Deployment Workflows

## Production Supervisor

The production entry point is:

```bash
quip-miner --config config.toml
```

The supervisor reads the backend inventory, starts one miner child for each configured backend group, and starts a telemetry aggregator when REST telemetry is enabled. Use this form for containers and production service managers because the config becomes the single source of truth.

To run only one configured group from a broader config:

```bash
quip-miner --config config.toml --mode gpu
```

`--mode` is a command-line narrowing option. It warns about configured groups that were dropped. There is no TOML equivalent.

## Direct Subcommands

Direct subcommands are useful for test/ops tooling and narrow interactive runs:

```bash
quip-miner cpu --validator ws://127.0.0.1:9944 --num-cpus 4 --signer-key ~/.quip-miner/signing.json
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend local --signer-key ~/.quip-miner/signing.json
quip-miner qpu --validator ws://127.0.0.1:9944 --daily-budget 30s --signer-key ~/.quip-miner/signing.json
```

They share the same startup guards: wallet funding/registration, descriptor filing, topology binding, solver registration when mempool is enabled, and chain sync/validator checks.

## Mode Resolution Commands

Use these before starting the supervisor:

```bash
quip-miner resolve-mode --config config.toml --default cpu
quip-miner resolve-modes --config config.toml --image-supports cpu,gpu
```

`resolve-mode` returns the single command a legacy one-mode entrypoint should run. `resolve-modes` returns all configured backend groups, one per line, for multi-child supervisor logic.

## Docker / Container Notes

Docker configs usually live at `/data/config.toml`, and the keystore at `/data/keystore.json`. The entrypoint generates a key once if missing, then treats the mounted `/data` volume as persistent state.

Important deployment rules:

- Back up `/data/keystore.json`; it controls the chain account.
- Publish REST telemetry only when intended: use `rest_host = "0.0.0.0"` inside containers and publish the port explicitly.
- Use sufficient shared memory for multiprocessing/shared-memory rings. The project docs recommend `--shm-size=2g` for Docker runs.
- There are no configuration environment variables for normal config values; edit the TOML.
- Multi-backend containers expose one telemetry surface by merging per-mode snapshot files.

Minimal CPU container TOML shape:

```toml
[miner]
signer_key = "/data/keystore.json"
rest_host = "0.0.0.0"
rest_port = 8086

[cpu]
num_cpus = 1
```

Minimal CUDA TOML shape:

```toml
[miner]
signer_key = "/data/keystore.json"
rest_host = "0.0.0.0"
rest_port = 8086

[gpu]
utilization = 100
yielding = false

[cuda.0]
```

## Systemd / Host Service Notes

The repository includes systemd-oriented material for operators, but host service installation mutates the machine. Do not run install/reload scripts automatically. Instead:

1. Generate or review the TOML.
2. Verify `quip-miner --help`, `quip-miner resolve-modes --config`, and config linting.
3. Ensure the service user can read the keystore and write logs/runtime directories.
4. Let the operator run host-mutating install commands manually.

## Live Validator Integration

A local validator under Docker compose is useful for live integration, but it starts services and may take time. Prefer parser/help/unit tests for skill verification. When a user explicitly wants live integration, use the documented validator WebSocket endpoint (`ws://127.0.0.1:9944`) and bootstrap dev chains only with `--seed-chain` after confirming they are dev/local chains.
