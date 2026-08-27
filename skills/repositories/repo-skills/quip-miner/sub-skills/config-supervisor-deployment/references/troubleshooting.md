# Config and Deployment Troubleshooting

## `CONFIG_ERROR: mempool is a per-miner property`

Cause: a legacy or guessed config put `mempool` in `[miner]`.

Fix:

```toml
# Wrong
[miner]
mempool = false

# Right
[cpu]
mempool = false
```

For GPU, put it in `[gpu]`, `[metal]`, or `[modal]`. For QPU, put it in the vendor section such as `[dwave]`.

## `config-conflict`

Cause: the TOML declares backend inventory and the CLI also tries to override that group.

Examples:

- `[cpu]` plus `quip-miner cpu --num-cpus 8`.
- `[cuda.0]` or `[gpu]` plus `quip-miner gpu --gpu-backend local`.
- `[dwave]` plus `quip-miner qpu --daily-budget 30s`.

Fix: choose one source of truth. Either remove the backend section and use CLI flags, or keep TOML inventory and omit conflicting flags.

## `validators` schema errors

`validators` must be a TOML list of strings:

```toml
[miner]
validators = ["ws://primary:9944", "wss://standby.example/rpc"]
```

A bare number or single string in the wrong shape fails early.

## `mempool = "false"` still not accepted

Quoted booleans are strings. Use unquoted booleans:

```toml
mempool = false
```

## Supervisor starts the wrong children

Run:

```bash
python scripts/quip_config_lint.py --config config.toml --json
quip-miner resolve-modes --config config.toml
```

Check which backend sections are present and whether `--mode` narrowed the run.

## Telemetry not reachable in Docker

- `rest_host = "127.0.0.1"` binds loopback inside the container and will not expose externally.
- Use `rest_host = "0.0.0.0"` inside the container and publish the port with Docker.
- Check `rest_port`; non-positive child sentinel values can disable per-child REST while the aggregator may still use a default.

## Shared memory or worker failures in containers

The miner uses worker processes and shared-memory rings. If workers fail unexpectedly in Docker, verify the container has enough shared memory; the project docs recommend `--shm-size=2g`.

## Systemd install uncertainty

Treat systemd installer scripts as operator-run host mutation. If a user asks whether to run them, first provide the command and expected effects, then let the operator execute it.
