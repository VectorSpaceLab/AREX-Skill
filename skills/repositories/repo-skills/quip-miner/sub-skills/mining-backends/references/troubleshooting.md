# Mining Backend Troubleshooting

## `--topology` rejected on live miner

Live miners derive topology from the chain's registered `DefaultTopology` and rebind when the chain changes. Do not pass `--topology` to `cpu`, `gpu`, or `qpu` live mining commands. Use standalone analysis tools for synthetic topologies.

## CUDA import succeeds but allocation fails

Run:

```bash
nvidia-smi
python - <<'PY'
import cupy as cp
print(cp.__version__)
print(cp.cuda.runtime.getDeviceCount())
cp.zeros(1)
PY
```

If allocation fails, check driver/container CUDA compatibility, device visibility, permissions, and container runtime GPU flags. Do not claim CUDA runtime verified until allocation passes.

## CUDA utilization/yielding confusion

`yielding=False` uses static budget behavior. `yielding=True` allows throttling/yield behavior but should not self-throttle based only on the miner's own NVML utilization. Config tests cover this path.

## Metal unavailable

Metal requires macOS Apple Silicon and Metal/PyObjC dependencies. On Linux, document config and host requirements only. There is no CPU fallback for live Metal mining.

## Modal unavailable

If `GPU.modal_sampler.GPU_AVAILABLE` is false, install/authenticate Modal before live jobs:

```bash
pip install modal
modal token new
```

Do not run cloud jobs without operator approval.

## QPU credentials or budget issues

- Set D-Wave credentials in the environment, not TOML.
- `daily_budget`, `min_block_budget`, `budget_cap`, and `qpu_initial_budget` control access-time pacing, not proof difficulty.
- `min_block_budget` must be less than or equal to `budget_cap`; if it exceeds the cap, a burst can never start.
- Frequent restarts can re-grant initial budget if configured that way; choose `qpu_initial_budget = "min"` for conservative operation.

## Mempool not participating

Check the elected owner group:

```bash
python scripts/quip_config_lint.py --config config.toml --json
```

QPU mempool defaults off. CPU/GPU default on unless set false. Only one group owns mempool for an account.

## Solver registration failure

Route to `../identity-wallet-bootstrap/references/solver-registration.md`. A stale or conflicting solver type can park mempool while PoW continues.

## Chain/topology mismatch

If mining fails because no topology is registered or topology hashes mismatch, bootstrap only dev chains with `--seed-chain`. Production topology is chain-side state. For proof/topology data validation, route to `../topology-proof-validation/SKILL.md`.
