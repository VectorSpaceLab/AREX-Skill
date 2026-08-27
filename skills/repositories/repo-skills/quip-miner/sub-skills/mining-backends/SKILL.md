---
name: mining-backends
description: "Use this quip-miner sub-skill for CPU, CUDA, Metal, Modal, and QPU
  mining commands, backend dependencies, QPU budgets, unified streaming, and
  PoW/mempool scheduling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Mining Backends

Use this sub-skill when the user needs to run, tune, or troubleshoot quip-miner CPU/GPU/QPU mining backends or understand PoW plus mempool scheduling on those workers.

## Route By Task

- **Backend commands and tuning:** Read `references/backend-workflows.md` for CPU SA, CUDA, Metal, Modal, D-Wave QPU, gate-model QPU, optional dependencies, and safe command patterns.
- **Streaming and mempool architecture:** Read `references/unified-streaming-and-mempool.md` for the stream-driver subprocess, shared-memory ring, feeder specs, PoW/mempool preemption, and no-inline-sampling invariant.
- **Backend failures:** Read `references/troubleshooting.md` for CUDA allocation, Metal host mismatch, Modal unavailable, QPU credential/budget, topology binding, and mempool-owner problems.
- **Availability probe:** Run `scripts/backend_probe.py --json` or the root `scripts/quip_backend_probe.py --json` before claiming backend availability.

## Common Commands

```bash
quip-miner cpu --validator ws://127.0.0.1:9944 --num-cpus 4 --signer-key ~/.quip-miner/signing.json
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend local --signer-key ~/.quip-miner/signing.json
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend metal --signer-key ~/.quip-miner/signing.json
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend modal --signer-key ~/.quip-miner/signing.json
quip-miner qpu --validator ws://127.0.0.1:9944 --qpu-type dwave --daily-budget 30s --signer-key ~/.quip-miner/signing.json
```

Prefer config-driven production runs (`quip-miner --config config.toml`) once the backend inventory is known.

## Key Rules

- Every worker mines PoW continuously. Mempool jobs preempt PoW on the same workers when the group owns mempool; PoW resumes afterward.
- CPU/GPU mempool defaults on; QPU mempool defaults off and must be explicitly opted into in the vendor section.
- A live miner pulls topology from the chain. Passing `--topology` to live mining commands is an error.
- CUDA guidance requires actual CUDA runtime evidence; a CPU import is not enough.
- Metal has no CPU fallback. On non-Apple hosts, provide config/docs guidance only.
- Do not run paid QPU sampling or Modal cloud jobs unless the operator explicitly accepts credentials, network, cost, and runtime.

## Boundaries

- Route TOML schema and supervisor deployment to `../config-supervisor-deployment/SKILL.md`.
- Route wallet, bootstrap, descriptor, and solver registration to `../identity-wallet-bootstrap/SKILL.md`.
- Route telemetry and attempts archives to `../telemetry-attempt-archive/SKILL.md`.
- Route topology/proof replay and D-Wave h/J range details to `../topology-proof-validation/SKILL.md`.
