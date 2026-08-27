# Solver Registration and Mempool Identity

Mempool participation requires a solver registration in `QuantumComputeMempool`. The miner startup guard uses `ensure_solver_registered` when the elected backend group participates in mempool.

## Query-first Contract

The guard first queries existing registration. This avoids burning a fee on a duplicate `register_solver` call, because the chain call is not idempotent.

Outcomes:

- `ALREADY_REGISTERED`: existing solver type matches the configured miner kind.
- `REGISTERED`: no existing registration; registration extrinsic landed.
- `RETYPED`: existing type differed, so the guard deregistered and registered the configured type.
- `FAILED`: RPC/chain/race errors that should park or disable the mempool side rather than crash PoW mining.

## One Account, One Solver Type

A single substrate account can hold one solver type. In multi-backend configs, every child derives the same mempool owner group from TOML:

1. Explicit `mempool = true` wins.
2. Default-on groups follow CPU then GPU order.
3. QPU defaults off because paid samples are opt-in.
4. Non-owner children are PoW-only.

If you want QPU to own mempool, set `mempool = false` in CPU/GPU groups and `mempool = true` in the QPU vendor section.

## Retyping Consequence

When the configured owner group changes, the guard can deregister and register the new type. That converges state but resets chain-side solver counters such as submitted solutions/rewards. Warn operators before changing a live account's solver type.

## Manual Commands

```bash
quip-miner register-solver --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json --miner-kind cpu
quip-miner register-solver --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json --miner-kind qpu_dwave
quip-miner deregister-solver --validator ws://127.0.0.1:9944 --signer-key ~/.quip-miner/signing.json
```

Use the miner-kind value that matches the backend group/vendor that will own mempool. Do not run multiple independent processes with the same signer and conflicting solver types.

## Mempool-fatal Behavior

If mempool submission hits a fatal receipt, the mempool side is parked for that run while PoW mining continues. This is deliberate: mempool is opportunistic and must not take down normal PoW participation.
