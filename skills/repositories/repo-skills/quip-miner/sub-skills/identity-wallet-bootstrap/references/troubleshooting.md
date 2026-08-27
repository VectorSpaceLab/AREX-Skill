# Identity and Bootstrap Troubleshooting

## Keystore already exists

`quip-miner keygen` refuses to overwrite by default. Use `--overwrite` only after confirming the existing account can be discarded or is backed up.

## Keystore permissions warning

The loader warns when a hybrid keystore is group/world-readable. Tighten permissions:

```bash
chmod 600 ~/.quip-miner/signing.json
```

## `wallet-underfunded`

The account balance is below the threshold and no suitable faucet/top-up was available.

Options:

- Provide `--faucet-url` for a dev/local faucet.
- On public testnet, rely on the canonical testnet faucet only when the chain name matches.
- Manually fund the account, then rerun `bootstrap`.

## Faucet failures

The bootstrap flow retries transient faucet failures such as 429/5xx/connection errors within a bounded timeout. A malformed request (400) is permanent. HTTP 403 can mean the faucet believes the account is already funded; compare the reported/free balance to the miner threshold.

## `validators-unreachable`

Every URL in the failover list failed. Check WebSocket scheme, validator port, DNS/firewall, and whether the node is still syncing or down. A bootstrap one-shot uses direct client failover rather than the long-running validator pool.

## `--seed-chain` refused

The chain name did not match dev/local prefixes. Do not try to bypass this guard for production; topology/difficulty seeding is dev-only.

## Descriptor validation errors

Common causes:

- Empty or too-long `node_name`.
- More than 8 RPC endpoints or oversized endpoint strings.
- Invalid public port.
- Secret-looking values such as pasted tokens or API keys.
- Solver names outside safe characters.

Use dry-run before submitting:

```bash
quip-miner identify --node-name rig-01 --miner-config config.toml --no-system-info --dry-run
```

## Solver type conflict

If another process with the same signer registers a different solver type, the guard reports failure instead of fighting it. Stop conflicting processes, decide the intended mempool owner, update TOML, then let startup converge registration.
