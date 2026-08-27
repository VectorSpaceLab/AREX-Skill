# Wallet, Bootstrap, and Node Identity

## Hybrid Keystore

`quip-miner keygen` writes a hybrid sr25519 + ML-DSA-44 signing keystore:

```bash
quip-miner keygen --out ~/.quip-miner/signing.json
```

Important behavior:

- Default path: `~/.quip-miner/signing.json`.
- `--overwrite` is required to replace an existing file.
- File mode should be `0o600`.
- The file contains a plaintext master seed plus cached public keys and account identifiers.
- Loading re-derives keys and rejects missing/mismatched cached public key fields.

Do not display the JSON contents to users. It contains secret key material.

## Bootstrap

`quip-miner bootstrap` performs a one-shot account setup:

```bash
quip-miner bootstrap \
  --validator ws://127.0.0.1:9944 \
  --signer-key ~/.quip-miner/signing.json
```

It is idempotent. The flow:

1. Load or create the signer keystore.
2. Connect to the validator list.
3. Optionally seed dev-chain difficulty/topology when `--seed-chain` is set.
4. Check account balance and use a faucet when configured or when the public testnet fallback applies.
5. Register the miner account if not already registered.
6. Print account/balance/registration summary.

Useful flags:

- `--validator URL` repeatable failover list.
- `--config config.toml` for `[miner]` defaults.
- `--signer-key PATH` overrides config/default signer path.
- `--faucet-url URL` uses a specific faucet when balance is low.
- `--seed-chain` and `--sudo-key` are dev-only topology/difficulty seeding tools.
- `--seed-topology M,T` selects Zephyr parameters for dev seeding.

## Dev-only Seeding

`--seed-chain` seeds `QuantumPow.Difficulty` and `QuantumPow.DefaultTopology` only on dev/local chain names. It should never be used against production networks. The default dev topology is small Zephyr Z(2,2); the production topology comes from chain governance/config.

## NodeDescriptor Identity

`quip-miner identify` submits a signed NodeDescriptor to `MinerRegistry.set_descriptor`. Dry-run prints the canonical JSON payload without submitting:

```bash
quip-miner identify \
  --validator ws://127.0.0.1:9944 \
  --signer-key ~/.quip-miner/signing.json \
  --node-name rig-01 \
  --rpc-endpoint ws://rig-01.example.com:9944 \
  --miner-config config.toml \
  --dry-run
```

Descriptor contents include:

- `node_name`, optional `public_host`/`public_port`, and repeatable `rpc_endpoints`.
- `auto_mine` marker and descriptor log level.
- Runtime block: Python, quip version, protocol version, Docker state.
- Miner inventory derived from backend config/specs.
- Optional `system_info` with CPU/GPU/memory/OS details.

Bounds and safety:

- `node_name` must be non-empty and at most 64 UTF-8 bytes.
- Up to 8 RPC endpoints, each at most 256 bytes.
- `public_host` max 253 bytes; `public_port` 1..65535.
- Secret-looking keys and values are scrubbed/rejected.
- Use `--no-system-info` in sandboxes or CI if hardware probes are not allowed.

## Startup Auto-identify

Mining startup runs descriptor filing after funding/registration. It retries a bounded number of times and verifies the on-chain payload hash. `node_name` defaults to hostname when neither CLI nor TOML sets it. Public host may be auto-detected via public IP services unless configured explicitly; set `public_host` in air-gapped/NAT/load-balanced deployments to avoid surprises.
