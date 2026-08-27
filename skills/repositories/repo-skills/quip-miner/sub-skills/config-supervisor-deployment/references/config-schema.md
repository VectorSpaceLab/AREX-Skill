# quip-miner TOML Config Schema

The v0.2 config has two top-level concerns:

1. `[miner]` — connection, signer, telemetry, identity, logging, faucet, and global submission/reward settings.
2. Backend inventory sections — top-level `[cpu]`, `[gpu]`, `[cuda.N]`, `[nvidia.N]`, `[metal]`, `[modal]`, `[qpu]`, `[dwave]`, `[ibm]`, `[braket]`, `[pasqal]`, `[ionq]`, and `[origin]`.

The package reads these with separate loaders (`load_miner_config` and `load_backend_config`), so do not nest backend inventory under `[miner]`.

## `[miner]` Keys

Common keys:

```toml
[miner]
validators = ["ws://validator-a:9944", "wss://validator-b.example/rpc"]
signer_key = "~/.quip-miner/signing.json"
faucet_url = "https://faucet.testnet.quip.network" # optional
rest_host = "127.0.0.1"                             # optional
rest_port = 8086                                    # optional; -1 disables child telemetry
node_name = "rig-01"                                # optional; defaults to hostname
public_host = "miner.example.com"                   # optional
public_port = 8086                                  # optional
log_level = "INFO"                                  # optional
node_log = "/var/log/quip-miner.log"                # optional rotating file handler
mempool_min_reward = 0                              # optional; 0 accepts all matching orders
```

Rules:

- `validators` must be a list of strings. CLI `--validator` is repeatable and overrides TOML when provided.
- `signer_key` points to the hybrid keystore created by `quip-miner keygen`.
- `listen` and `port` are v0.1 aliases for `rest_host` and `rest_port`; canonical keys win when both are present.
- `[miner] mempool` is rejected. Move it into the backend section it applies to.
- `mempool_min_reward` remains global and must be a non-negative integer.

## `[submission]` Keys

Proof submission tuning lives in `[submission]`:

```toml
[submission]
tip_plancks = 0
max_retries = 3
retry_backoff_ms = 250
```

`tip_plancks` must be a non-negative integer no larger than the chain `u128` balance range. Retries are additional attempts after the first submit; backoff is per-attempt linear delay in milliseconds.

## CPU Inventory

```toml
[cpu]
num_cpus = 4
# mempool = false
```

CPU mempool defaults on. Set `mempool = false` in `[cpu]` to make CPU workers PoW-only.

## GPU Inventory

Shared GPU defaults go in `[gpu]`; per-device sections declare actual devices:

```toml
[gpu]
utilization = 100
yielding = false
sms_per_nonce = 4
# mempool = false

[cuda.0]
[cuda.1]
# or [nvidia.0] as an alias
```

Metal and Modal are group-level inventory sections:

```toml
[metal]
utilization = 100
yielding = true
active_util = 85
idle_after_s = 60

[modal]
gpu_type = "a10g"
```

GPU mempool defaults on. Put `mempool = false` in `[gpu]`, `[metal]`, or `[modal]` to move mempool ownership away from the GPU group.

## QPU Inventory

QPU vendor sections carry provider-specific settings. Credentials come from environment variables or provider profiles, not TOML.

```toml
[dwave]
daily_budget = "30m"
min_block_budget = "90s"
qpu_initial_budget = "min"
solver = "Advantage2_system1"
region = "na-west-1"
# mempool = true  # paid QPU mempool is opt-in
```

Gate-model sections (`[ibm]`, `[braket]`, `[pasqal]`, `[ionq]`, `[origin]`) follow the same pattern for provider-specific budget/token configuration. Prefer environment references/profiles over literal tokens.

## Mempool Owner Election

One account can register one solver type. The config elects one mempool owner group:

1. Any explicit `mempool = true` group outranks default-on groups.
2. Ties break in canonical order: CPU, GPU, QPU.
3. CPU/GPU default on; QPU default off.
4. Every non-owner child resolves mempool off from the same TOML.

Use explicit `mempool = false` in a section to move ownership to the next group.

## CLI-vs-TOML Conflicts

If a backend section exists in TOML, do not pass a conflicting CLI inventory flag for that backend group:

- `[cpu]` conflicts with `--num-cpus`.
- `[gpu]`, `[cuda.N]`, `[metal]`, or `[modal]` conflict with `--gpu-backend`.
- `[dwave]` or other QPU vendor sections conflict with `--qpu-type` or `--daily-budget`.

This fail-fast rule prevents ambiguous deployments.
