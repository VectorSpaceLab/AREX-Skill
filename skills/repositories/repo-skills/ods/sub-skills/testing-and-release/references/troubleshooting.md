# ODS validation troubleshooting

Use this when a selected ODS validation lane fails or cannot run. First determine whether the failure is a product regression, a missing local prerequisite, a CI-only environment issue, or an intentionally expensive lane being run on the wrong host.

## Quick failure triage

| Symptom | Likely cause | Action |
|---|---|---|
| `make lint` fails during `bash -n` | shell syntax error in a changed script, often from Bash-version assumptions | Run `bash -n <changed files>` directly; for macOS-sensitive installer code also check `/bin/bash -n` or the matrix-smoke Bash 3.2 lane. |
| ShellCheck CI fails but `make lint` passes | `make lint` is syntax only; `lint-shell.yml` adds ShellCheck and localhost curl guard | Reproduce ShellCheck with the workflow's excludes/severity. Replace `curl http://localhost:` with `127.0.0.1` in executable shell scripts unless the workflow documents an exclusion. |
| Ruff/type-check workflow fails | Python style/type issue not covered by `make lint` | Run the workflow command for the changed subtree. Type-check steps may be `continue-on-error` but still indicate quality debt. |
| `validate-env.sh` exits `3` | missing Bash 4+, jq, env file, or schema file | Use modern Bash on macOS, install jq, and pass readable input files. Exit `2` means validation errors; exit `3` means prerequisites/input. |
| `validate-env.sh` exits `2` | required/unknown key, type, enum, range, length, duplicate, or runtime-contract error | Fix the reported line. It parses `.env` safely instead of sourcing it, so shell interpolation does not hide bad values. |
| `validate-manifests.sh` warns about Python modules | PyYAML/jsonschema unavailable, so strict schema validation is skipped or reduced | Install PyYAML and jsonschema for strict checks, then rerun `bash scripts/validate-manifests.sh` and related tests. |
| `validate-compose-stack.sh` says Docker Compose not found | Docker CLI plugin or legacy `docker-compose` missing | Install Docker Compose or run a non-Docker focused lane first. The script validates config; it does not start services. |
| `docker compose config` fails on missing env vars | compose references required secrets/ports not set | Use documented CI placeholder env values for config validation. Do not invent or leak real secrets. |
| `tests/run-bats.sh` tries to clone BATS | BATS vendored checkout is missing | Allow network clone, preinstall BATS, or run a narrower non-BATS lane if offline. |
| Dashboard UI lane fails before tests | Node/npm dependency install or lockfile issue | Use `npm ci` from `ods/extensions/services/dashboard`; lockfile drift belongs with the dashboard sub-skill. |
| Dashboard API lane fails importing app | service requirements missing or wrong working directory | Install requirements in `ods/extensions/services/dashboard-api` and run pytest from that directory. |
| `scripts/simulate-installers.sh` fails in doctor or macOS simulation | host lacks optional diagnostic tools or simulation preflight blockers | Read the generated summary and failing sub-run; separate simulation harness prerequisites from installer contract regressions. |
| `scripts/validate.sh` cannot reach services | it is a post-install validation script and expects a running stack | Do not use it as source-only validation. Use it only when an installed/running ODS stack is the target. |
| Fleet runner blocks on lock | another heavy ODS fleet job is using the shared host lock | Wait, set a bounded `--lock-timeout`, or coordinate with the operator. Use `--no-host-lock` only for local debugging when no full fleet can collide. |
| Incus VM lane fails before ODS checks | Incus not initialized, user lacks access, nested virtualization/network unavailable | Fix the host lab first; do not mark ODS broken until VM prerequisites are healthy. |
| Gitleaks finding in a fixture/template | fixture resembles a secret | Prefer redaction or generated placeholders. Only update `.gitleaks.toml` allowlists for documented non-secret templates and rerun scans. |

## Missing dependency guide

| Lane | Common dependencies | Notes |
|---|---|---|
| `make lint` | Bash, Python 3 | Shell syntax over all `.sh` files plus Python compile of dashboard API entry modules. |
| `tests/test-validate-env.sh` / `scripts/validate-env.sh` | Bash 4+, jq | macOS system Bash is 3.2; run via a newer Bash for validator checks. |
| `scripts/validate-manifests.sh` | jq; Python 3 with PyYAML/jsonschema for strict schema | Without Python modules, compatibility checks may run but schema depth is reduced. |
| Extension audit | Python 3, PyYAML/jsonschema depending on audit path | Use the services-and-extensions sub-skill for manifest semantics. |
| Compose validation | Docker CLI + Compose plugin or `docker-compose` | `config` is safer than `up`, but still host-tool dependent. |
| BATS | Git/network for auto-vendoring when missing | `tests/run-bats.sh` clones bats-core/support/assert into the tests area if absent. |
| Dashboard UI | Node 20-compatible npm environment | CI uses `npm ci`, then lint/test/build. |
| Dashboard API | Python 3.11-compatible env and service requirements | CI installs `requirements.txt` and `tests/requirements-test.txt`. |
| PowerShell | `pwsh`, PSScriptAnalyzer | Windows-only tests need a Windows runner. |
| Fleet distro | Docker daemon, network, disk, host lock | Pulling 10 distro images is heavy and can fail from registry/network issues. |
| Fleet VM | Incus, KVM/QEMU, systemd-capable images, network, host lock | Expensive; use for systemd/Docker daemon realism, not routine PR checks. |

## CI-only or platform-specific failures

- **macOS Bash 3.2:** `matrix-smoke.yml` checks installer scripts with `/bin/bash -n`. Avoid Bash features unsupported by 3.2 in portable installer surfaces, or route platform-specific code correctly.
- **Windows PowerShell:** Ubuntu PowerShell lanes catch syntax/analyzer issues, but Windows footprint/runtime contracts only run on Windows. Do not claim Windows runtime evidence from Linux-only lanes.
- **Distro matrix network flakes:** package manager retries and zypper tuning exist because registry/repository access can be flaky. Reproduce with the specific distro container before rewriting product code.
- **Docker Desktop / WSL2:** Windows support is a real platform path, but current release evidence requires Windows target artifacts. Keep code support separate from candidate evidence.
- **Incus nested Docker:** Arch/openSUSE VM lanes can expose lab limitations. Use container and real-hardware results to decide whether the bug is in ODS or the lab.

## Full gate and fleet cautions

Do not jump from a small change to the heaviest lane unless the changed surface requires it.

| Lane | Why it is expensive | Safer first step |
|---|---|---|
| `make gate` | Runs broad Makefile stack: lint, test, BATS, smoke, simulation | Run owner-focused tests and `make lint` first. |
| `scripts/release-gate.sh` | Release checklist with compatibility, claims, contracts, smoke, simulation, update rollback | Run the specific release/contract step that maps to the change. |
| `make fleet-distros` | Pulls/runs many Docker distro containers and takes a host lock | Run matrix-smoke equivalent or one targeted distro. |
| `make fleet-vms` | Boots Incus VMs, installs dependencies/Docker, runs installer dry-run | Use only for systemd/Docker-daemon issues containers cannot prove. |
| Real-hardware fleet | Fresh installs, GPU runtime, dashboard/Hermes/model/capability/lifecycle checks | Required for release/User Green claims; not a local development default. |
| Post-install validation scripts | Need live stack, ports, Docker services, and possibly models | Use after install or when debugging an existing deployment. |

## Secret and release evidence hygiene

- Keep ephemeral credentials, generated secrets, local paths, hostnames, LAN addresses, and raw fleet logs out of public reports and runtime instructions.
- Use redacted gitleaks reports for triage and remove real secrets from history if needed.
- Release notes should cite sanitized hardware classes, run date, commit/tag, summaries, and skipped/deferred surfaces instead of private artifact paths.
- If a release report is re-adjudicated after an `OVERALL: FAIL`, the new report must disclose the old result, corrected rule, reason, and affected artifacts. Do not silently relax validators.

## When a lane fails after a multi-area change

1. Split the changed paths by owner sub-skill.
2. Reproduce each failing command directly from the correct working directory.
3. Decide whether the failure is in test harness/fixtures, implementation, or environment.
4. Route implementation fixes to the owning sub-skill, then return here to choose the next validation lane.
5. Escalate to `make gate`, release gate, or fleet only after focused lanes are green or when the remaining risk is specifically install/runtime/release evidence.
