# Testing and CI

## Safe Targeted Test Map

| Workflow touched | Suggested tests | Notes |
| --- | --- | --- |
| TOML config, mode resolution, mempool owner | `python -m pytest tests/test_miner_config.py -q` | Fast parser and pure config behavior. |
| CLI construction, topology parsing, command routing | `python -m pytest tests/test_quip_cli.py -q` | Uses Click runner/mocks; avoids live mining. |
| Keystore, hybrid signatures, descriptor identity | `python -m pytest tests/test_hybrid_signer.py tests/test_system_info.py -q` | Covers pinned constants, tamper checks, descriptor bounds/scrubbing. |
| Bootstrap/faucet/registration state machine | `python -m pytest tests/test_miner_bootstrap.py -q` | Prefer mocked tests before live validator. |
| Solver registration | `python -m pytest tests/test_solver_registration.py -q` | Verifies query-first/race/retype behavior. |
| Telemetry process and snapshot aggregation | `python -m pytest tests/test_telemetry_process.py -q` | Starts local aiohttp process on loopback; no live chain needed for selected cases. |
| Mining snapshot SCALE decode/topology sizes | `python -m pytest tests/test_mining_snapshot_decode.py -q` | Pure decode tests and topology-size guards. |
| CUDA scheduler/config behavior | `python -m pytest tests/test_gpu_scheduler.py -q` | Requires CuPy/CUDA availability; otherwise skip or record backend block. |
| Modal streaming behavior | `python -m pytest tests/test_modal_streaming.py -q` | Check whether tests are stubbed/safe before running cloud-auth paths. |
| Pool/client failover | `python -m pytest tests/test_pool_client.py -q` | Mocked networking; useful for validator failover changes. |

Run `python -m pytest tests/ -v` only when a broad suite is appropriate and optional backend/hardware skips are understood.

## No-inline-sampling CI Guard

The unified streaming stack removed inline sampling. Run:

```bash
python scripts/lint_no_inline_sampling.py --repo-root <checkout>
```

The guard scans `shared`, `QPU`, `GPU`, `CPU`, and `substrate` for:

- `def _sample(`
- `def _sample_batch(`
- `STREAMING_PUMP`
- `DRIVER_OWNS_FEEDER`

If any reappear, the change violates the architecture and should be redesigned through `StreamContext` + shared-memory ring.

## Test Safety Policy

Prefer tests that are:

- short and deterministic;
- no network/validator/cloud credentials;
- no paid QPU access;
- no destructive writes outside temp dirs;
- no broad Docker/systemd side effects.

Record these statuses distinctly in reviews: PASS, NATIVE_FAIL, SKIP_UNSAFE, SKIP_NOT_SELECTED, and BLOCKED_REQUIRED_BACKEND. Do not count optional skips as passes.

## CI / Docker Notes

The repository CI builds CPU and CUDA Docker images and runs packaging checks. Docker live validator integration is useful for operators but not required for every source change. Container miner runs need sufficient shared memory because workers use multiprocessing and shared-memory rings.
