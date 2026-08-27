---
name: maintainer-testing-release
description: "Use this quip-miner sub-skill for maintainer pytest selection, CI
  invariants, no-inline-sampling lint, multiprocessing/hang debugging,
  versioning, Docker/PyInstaller release checks, and safe benchmark policy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Maintainer Testing and Release

Use this sub-skill when changing quip-miner source, selecting targeted tests, preserving architecture invariants, debugging hung processes, or preparing release/build validation.

## Route By Task

- **Targeted tests and CI:** Read `references/testing-and-ci.md` for safe pytest selections by workflow, no-inline-sampling guard, Docker/build CI notes, and test safety classification.
- **Release and packaging:** Read `references/release-and-packaging.md` for versioning, PyInstaller build/selftest, Docker images, and release checks.
- **Failures and hangs:** Read `references/troubleshooting.md` for faulthandler/SIGABRT, multiprocessing teardown, no-threads rule, optional backend skips, and benchmark safety.
- **No-inline-sampling lint:** Run `scripts/lint_no_inline_sampling.py --repo-root <checkout>` when changing `shared/`, `CPU/`, `GPU/`, `QPU/`, or `substrate/` sampling paths.

## Common Commands

```bash
python -m pytest tests/test_miner_config.py -q
python -m pytest tests/test_quip_cli.py -q
python -m pytest tests/test_hybrid_signer.py tests/test_system_info.py -q
python -m pytest tests/test_telemetry_process.py -q
python -m pytest tests/test_gpu_scheduler.py -q
python scripts/lint_no_inline_sampling.py --repo-root <checkout>
quip-miner selftest
```

Use the narrowest relevant tests first. Do not run live QPU benchmarks, Docker compose validator integration, or host-mutating deployment scripts unless the operator explicitly asks.

## Key Rules

- New background work in this repo should use multiprocessing (`spawn`) or asyncio, not new `threading.Thread` workers.
- Threads from third-party libraries or existing stdlib internals can exist, but document exceptions inline when relevant.
- The unified streaming stack is mandatory. Reintroduced inline sampling symbols are a regression.
- Enable faulthandler before long or potentially wedged Python runs; use SIGABRT for traceback dump on hard hangs.
- For CUDA changes, run actual CUDA tests only when compatible hardware/dependencies exist. Record optional backend skips separately from passes.

## Boundaries

- Route operator config/deployment tasks to `../config-supervisor-deployment/SKILL.md`.
- Route live mining behavior to `../mining-backends/SKILL.md`.
- Route topology/proof data tools to `../topology-proof-validation/SKILL.md`.
- Route telemetry runtime diagnosis to `../telemetry-attempt-archive/SKILL.md`.
