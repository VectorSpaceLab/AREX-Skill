---
name: identity-wallet-bootstrap
description: "Use this quip-miner sub-skill for hybrid keystores, wallet funding
  and miner registration, bootstrap, NodeDescriptor identify, auto-identify, and
  mempool solver registration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Identity, Wallet, Bootstrap, and Solver Registration

Use this sub-skill when the user needs to create or load a signing wallet, bootstrap a miner account, submit or preview a NodeDescriptor, reason about faucet/dev-chain seeding, or manage QuantumComputeMempool solver registration.

## Route By Task

- **Keystore and bootstrap:** Read `references/wallet-bootstrap-identity.md` for `quip-miner keygen`, `bootstrap`, signer file safety, validators, faucet top-up, dev-only `--seed-chain`, and idempotent account registration.
- **NodeDescriptor identity:** Use the same reference plus `scripts/descriptor_preview.py` to build/dry-run descriptor payloads from config without submitting.
- **Solver registration:** Read `references/solver-registration.md` for query-first registration, retyping, one-account/one-solver constraints, and mempool owner consequences.
- **Failures:** Read `references/troubleshooting.md` for underfunded wallets, validators unreachable, unsafe dev seeding, descriptor validation failures, and solver type conflicts.

## Common Commands

```bash
quip-miner keygen --out ~/.quip-miner/signing.json
quip-miner bootstrap --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json
quip-miner identify --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json --node-name rig-01 --miner-config config.toml --dry-run
quip-miner register-solver --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json --miner-kind cpu
quip-miner deregister-solver --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json
```

Prefer `identify --dry-run` or the bundled descriptor preview helper before submitting identity data.

## Key Rules

- The keystore is hybrid sr25519 + ML-DSA-44 and stores the plaintext 32-byte master seed. Keep permissions tight and back it up.
- `bootstrap` is idempotent against an already funded/registered account.
- `--seed-chain` is dev-only. It must be refused for non-dev chain names and never used for production chains.
- NodeDescriptor `node_name` is required for manual `identify`; startup auto-identify defaults to the hostname when not configured.
- Descriptor payloads scrub secret-looking keys/values, but users should still keep secrets out of configs.
- Solver registration is query-first. If the configured mempool owner type changes, the guard can deregister and register the new type, resetting solver counters.

## Boundaries

- Route TOML schema and mempool owner election mechanics to `../config-supervisor-deployment/SKILL.md`.
- Route backend runtime choices and mempool scheduling to `../mining-backends/SKILL.md`.
- Route telemetry surfaces showing descriptor/status to `../telemetry-attempt-archive/SKILL.md`.
