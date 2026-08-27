---
name: quip-miner
description: "Use this repo skill for QuIP quip-miner, the Substrate-integrated
  quantum mining CLI, when configuring or operating CPU/CUDA/Metal/Modal/QPU
  miners, managing hybrid wallets/bootstrap/identity, telemetry, topology/proof
  validation, deployment, or maintainer tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# QuIP Miner Repo Skill

Use this skill when a task involves the `quip-miner` command, the `quip-protocol` Python package, QuIP quantum proof-of-work mining, Substrate validator integration, miner configuration, hybrid signing wallets, telemetry, topology/proof tools, or repo maintenance for this codebase.

## First Checks

- Python: 3.10+.
- Package identity check:

  ```bash
  python -c "from importlib.metadata import version; import quip_cli; print(version('quip-protocol'))"
  ```

- CLI check:

  ```bash
  quip-miner --help
  ```

- From a source checkout, install only the extras needed for the target backend:

  ```bash
  python -m pip install -e .          # base + CPU/QPU package surface
  python -m pip install -e '.[cuda]'  # NVIDIA CUDA backend
  python -m pip install -e '.[metal]' # Apple Silicon Metal backend
  python -m pip install -e '.[dev]'   # pytest and pytest-asyncio
  ```

- Quick environment probe:

  ```bash
  python scripts/quip_backend_probe.py --json
  ```

Read `references/installation-and-environment.md` before diagnosing optional dependencies or backend availability.

## Route By Task

- **Config, supervisor, and deployment:** Use `sub-skills/config-supervisor-deployment/SKILL.md` for TOML schema, `[miner]` vs backend sections, `resolve-mode(s)`, top-level `quip-miner --config`, Docker `/data/config.toml`, telemetry bind settings, and systemd/container caveats.
- **Wallet, bootstrap, identity, and solver registration:** Use `sub-skills/identity-wallet-bootstrap/SKILL.md` for `keygen`, `bootstrap`, faucet/dev seeding, NodeDescriptor `identify`, signer file safety, and mempool solver registration/deregistration.
- **Mining backends:** Use `sub-skills/mining-backends/SKILL.md` for `quip-miner cpu`, `gpu`, `qpu`, CPU SA, CUDA, Metal, Modal, D-Wave/gate-model QPUs, QPU budget knobs, unified streaming, and PoW/mempool scheduling.
- **Telemetry and attempt archive:** Use `sub-skills/telemetry-attempt-archive/SKILL.md` for `/api/v1` endpoints, snapshot aggregation, node health checks, `QUIP_RUNTIME_DIR`, `QUIP_MINING_ATTEMPTS_DIR`, and per-solution mining attempt/solution archives.
- **Topology and proof validation:** Use `sub-skills/topology-proof-validation/SKILL.md` for `dwave_topologies`, Advantage2/Zephyr topology files, D-Wave h/J ranges, proof-chain download/revalidation, and dumped BQM records.
- **Maintainer testing and release:** Use `sub-skills/maintainer-testing-release/SKILL.md` for targeted pytest, CI invariants, no-inline-sampling lint, PyInstaller `selftest`, versioning, and hang-debugging procedures.

## Shared Operating Rules

- `quip-miner --config config.toml` is the production entry point. Direct subcommands (`cpu`, `gpu`, `qpu`) are useful for focused runs and tests.
- `--mode cpu|gpu|qpu` is CLI-only narrowing for a multi-backend config; there is no config-file key for mode selection.
- Mempool participation is config-only and per backend group: put `mempool = false` or `true` inside `[cpu]`, `[gpu]`, `[metal]`, `[modal]`, or a QPU vendor section such as `[dwave]`. A `[miner] mempool` key is invalid.
- CPU and GPU mempool default on; QPU mempool defaults off because paid samples are opt-in. One substrate account can register one solver type, so the config elects exactly one mempool owner group.
- Live miners pull the registered topology from the chain; do not pass `--topology` to live mining commands.
- Never store QPU/cloud credentials in TOML. D-Wave uses environment variables such as `DWAVE_API_KEY`; other providers use their own environment/profile mechanisms.
- The runtime architecture is unified streaming: every backend and both PoW/mempool jobs use a stream-driver subprocess plus shared-memory ring. Do not reintroduce inline `_sample`/`_sample_batch` mining paths.
- Use multiprocessing for new background work in this repo; do not add new `threading.Thread`-based mining or telemetry workers.

## Validation Pattern

1. Run package/CLI checks from **First Checks**.
2. Route to the owning sub-skill and run its safe helper script or command-builder.
3. Prefer config/parser/help/import tests before live validator, Docker, cloud, or QPU runs.
4. For CUDA claims, verify an actual CUDA runtime; a CPU import is not proof of CUDA execution.
5. For Metal, Modal, and QPU claims, state hardware/auth/cost requirements and do not run live jobs unless the operator explicitly approves.
6. For repo changes, run the narrowest relevant pytest selection plus `python sub-skills/maintainer-testing-release/scripts/lint_no_inline_sampling.py --repo-root <checkout>` when sampling code changed.

## Shared References

- `references/installation-and-environment.md` — install extras, first checks, backend availability, package facts.
- `references/troubleshooting.md` — cross-cutting installation, validator, config, secrets, telemetry, and backend failures.
- `references/repo-provenance.md` — source snapshot and evidence paths used to build this skill; refresh when the repository drifts.
- `references/repo-routing-metadata.json` — structured router metadata for managed repo-skill import.
