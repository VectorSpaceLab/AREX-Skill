# Repository Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from repository evidence for the QuIP Protocol `quip-miner` / `quip-protocol` Python package.

## Source Snapshot

| Field | Value |
| --- | --- |
| VCS | git |
| Commit | `72a7e77a31fbbf6797d63dd9462b9038fb19b710` |
| Branch | `main` |
| Exact tag | `v0.2.1` |
| Remote URL | omitted-private-or-unknown |
| Working tree state at generation | dirty: generated `skills/` review/runtime artifacts were untracked or ignored during skill creation; source evidence files otherwise matched the recorded commit |
| Package distribution | `quip-protocol` |
| Package version observed during inspection | `0.2.1` |

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `MINER_README.md`
- `ARCHITECTURE.md`
- `docs/miner-architecture.md`
- `docs/metal-gpu-governor.md`
- `docs/dwave-solver-ranges.md`
- `docs/VERSIONING.md`
- `quip_cli.py`
- `shared/miner_config.py`
- `shared/miner_core.py`
- `shared/miner_worker.py`
- `shared/stream_context.py`
- `shared/ring_views.py`
- `shared/stats_snapshot.py`
- `shared/mining_attempt_log.py`
- `shared/keystore_hybrid.py`
- `shared/hybrid_signer.py`
- `shared/system_info.py`
- `substrate/client.py`
- `substrate/pool.py`
- `substrate/miner_bootstrap.py`
- `substrate/solver_registration.py`
- `substrate/telemetry_process.py`
- `CPU/`
- `GPU/`
- `QPU/`
- `dwave_topologies/`
- `quip-miner.example.toml`
- `quip.network.cpu.example.toml`
- `quip.network.gpu.example.toml`
- `quip.network.qpu.example.toml`
- `docker/README.md`
- `docker/entrypoint.sh`
- `docker/quip-miner.cpu.toml`
- `docker/quip-miner.cuda.toml`
- `docker/docker-compose.yml`
- `systemd-linux/README.md`
- `pyinstaller/build.sh`
- `tests/test_miner_config.py`
- `tests/test_quip_cli.py`
- `tests/test_hybrid_signer.py`
- `tests/test_system_info.py`
- `tests/test_miner_bootstrap.py`
- `tests/test_solver_registration.py`
- `tests/test_gpu_scheduler.py`
- `tests/test_modal_streaming.py`
- `tests/test_telemetry_process.py`
- `tests/test_mining_snapshot_decode.py`
- `tools/check-node.sh`
- `tools/validate_mined_topology.py`
- `tools/download_and_validate_wins.py`
- `tools/dump_solver_ranges.py`
- `tools/lint_no_inline_sampling.py`

## Refresh Guidance

Refresh this skill when any of these change substantially:

- `quip-miner` CLI options, subcommands, config merge/conflict behavior, or production supervisor semantics.
- Mempool defaults, solver registration behavior, backend-group election, or one-account/one-solver constraints.
- Hybrid keystore format, NodeDescriptor schema, secret scrubbing, bootstrap/faucet behavior, or dev-chain seeding rules.
- CPU/CUDA/Metal/Modal/QPU backend factories, optional dependency names, QPU budget semantics, Metal governor behavior, or unified streaming architecture.
- Telemetry endpoint routes, stats snapshot shape, attempt archive layout, solution-number semantics, or archive query parameters.
- Topology files/embeddings, proof validation format, D-Wave solver ranges, allowed value specs, or BQM dump schema.
- CI/test expectations, release/versioning policy, PyInstaller bundling/selftest behavior, or no-inline-sampling guard patterns.
