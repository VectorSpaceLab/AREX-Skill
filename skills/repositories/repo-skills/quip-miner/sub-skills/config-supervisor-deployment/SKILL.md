---
name: config-supervisor-deployment
description: "Use this quip-miner sub-skill for TOML configuration, production
  supervisor mode, mode resolution, Docker/container deployment, telemetry bind
  settings, and safe deployment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Config, Supervisor, and Deployment

Use this sub-skill when the user needs to create, migrate, lint, or explain a `quip-miner` TOML config; choose direct subcommands vs production supervisor mode; run a Docker/container deployment; or diagnose config-mode conflicts.

## Route By Task

- **TOML schema and validation:** Read `references/config-schema.md` for `[miner]`, `[submission]`, backend inventory tables, validators, signer key, telemetry, aliases, and mempool placement.
- **Production supervisor and deployment:** Read `references/supervisor-and-deployment.md` for `quip-miner --config`, `--mode` narrowing, Docker `/data/config.toml`, shared memory, entrypoint behavior, and systemd cautions.
- **Config errors:** Read `references/troubleshooting.md` for malformed TOML, invalid `[miner] mempool`, backend conflict errors, invalid validators, and submission tip/retry validation.
- **Template generation:** Use `scripts/render_config_template.py` to draft a safe CPU/CUDA/QPU TOML skeleton, then use the root `scripts/quip_config_lint.py` against the active installed package.

## Key Rules

- Production mode is `quip-miner --config config.toml`; the supervisor starts one child per declared backend group and a telemetry aggregator when REST is enabled.
- Direct subcommands (`quip-miner cpu`, `gpu`, `qpu`) accept CLI flags for focused runs, but if the TOML already declares a backend group, conflicting CLI inventory flags fail fast.
- `--mode cpu|gpu|qpu` narrows a multi-backend config at runtime. It is CLI-only and must not be written into TOML.
- `[miner]` is for connection, signer, faucet, telemetry, identity, logging, and global submission/reward thresholds. Hardware inventory lives in top-level backend sections.
- `mempool` belongs inside backend sections, not `[miner]`. CPU/GPU default on; QPU default off.
- Do not put credentials in config files. QPU/cloud credentials belong in environment variables or provider profiles.

## Boundaries

- Route wallet creation, faucet/bootstrap, NodeDescriptor submission, and solver registration to `../identity-wallet-bootstrap/SKILL.md`.
- Route backend tuning semantics such as CUDA utilization, Metal governor, Modal auth, or QPU budget pacing to `../mining-backends/SKILL.md`.
- Route telemetry endpoint diagnosis and snapshot files to `../telemetry-attempt-archive/SKILL.md`.
- Route maintainer tests and release packaging to `../maintainer-testing-release/SKILL.md`.

## Safe Checks

```bash
python scripts/render_config_template.py --backend cpu --num-cpus 4
python scripts/render_config_template.py --backend cuda --cuda-devices 0,1 --rest-port 8086
python scripts/quip_config_lint.py --config config.toml --json
quip-miner resolve-modes --config config.toml
```

Do not start live miners solely to validate TOML shape; parser and mode-resolution checks are safer first.
