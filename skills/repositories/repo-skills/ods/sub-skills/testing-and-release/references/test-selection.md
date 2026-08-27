# ODS test selection reference

This reference turns changed ODS paths into focused validation lanes. It is self-contained operating guidance distilled from the ODS Makefile, tests, validation scripts, and public validation docs. Commands assume an ODS source checkout whose inner product directory is `ods/`.

## Decision model

1. **Classify the changed surface.** Use the bundled selector or the path matrix below.
2. **Run the narrowest safe native candidate first.** Prefer direct tests, static checks, and contract scripts over broad gates.
3. **Escalate only for risk.** Smoke, simulation, Docker, post-install, fleet, and real-hardware lanes are broader, slower, or host-dependent.
4. **Keep release claims separate from source tests.** A green source-level lane does not prove a live install, GPU runtime, or User Green release status.

Safety classes used below:

| Class | Meaning | Default? |
|---|---|---|
| `read-only/static` | Parses files, compiles code, checks docs/config, no service start | yes |
| `safe-runnable` | Runs repo-owned unit/contract scripts; may need Python/Node/JQ deps | yes when relevant |
| `needs-docker-config` | Uses Docker/Compose for config or lightweight container behavior | ask if Docker availability matters |
| `post-install` | Requires a running or installed ODS stack | no by default |
| `expensive` | Broad gate, simulation, distro fleet, Incus VM, real hardware, or model/runtime exercise | no by default |
| `host-mutating` | Installs, starts services, downloads models, changes host state, or performs lifecycle operations | only with explicit user intent |

## Make targets

| Target | Native command | What it covers | Safety / cost | Use when |
|---|---|---|---|---|
| `lint` | `cd ods && make lint` | `bash -n` over shell files plus Python compile check for dashboard API entry modules | read-only/static | almost any shell/Python change |
| `test` | `cd ods && make test` | many unit/contract tests: install docs, tier map, installer contracts, env/config, CLI, rootless, AMD/Lemonade, overlay/plist, mode, migration, update, fleet-contract regressions | safe-runnable but broad | before merging broad source changes when focused lanes are green |
| `bats` | `cd ods && make bats` | BATS unit tests through `tests/run-bats.sh` | safe-runnable; may clone BATS if missing | shell library/CLI parser changes |
| `smoke` | `cd ods && make smoke` | static platform smoke scripts for AMD, NVIDIA, WSL, and macOS dispatch | moderate; still source-level | installer/platform support or release claim changes |
| `simulate` | `cd ods && make simulate` | Linux dry-run, macOS installer simulation, Windows preflight simulation, doctor snapshot, simulation summary validation | moderate/expensive; writes local artifacts | installer/platform/release path changes after focused tests |
| `fleet-distros` | `cd ods && make fleet-distros` | Docker multi-distro package-manager, syntax, resolver, and dry-run checks | expensive; needs Docker daemon and host lock | release-risk Linux installer/distro changes |
| `fleet-vms` | `cd ods && make fleet-vms` | Incus VM systemd + Docker daemon + installer dry-run lanes | expensive; needs Incus/KVM and host lock | systemd/Docker lifecycle regressions that containers cannot prove |
| `verify-bootstrap` | `cd ods && make verify-bootstrap EXPECTED_REF=<git-ref>` | hosted bootstrap bytes against exact ref | network-dependent | bootstrap alias or public install URL changes |
| `doctor` | `cd ods && make doctor` | local diagnostic report | host-inspecting; may reveal local environment details | installed-system diagnostics, not routine source checks |
| `gate` | `cd ods && make gate` | `lint + test + bats + smoke + simulate` | expensive broad pre-release lane | near-final confidence, not default development validation |

`ods/scripts/release-gate.sh` is a separate release checklist script. It runs shell syntax, compatibility and release-claim checks, selected contracts, smoke scripts, installer simulation, and update rollback. Do not assume it is identical to `make gate`.

## Path-to-lane matrix

Use the most specific row that matches. If a change spans rows, combine the focused lanes before choosing a broad gate.

| Changed surface | Owner sub-skill | Focused lanes | Broader or optional lanes | Notes |
|---|---|---|---|---|
| `README.md`, `ods/README.md`, `ods/docs/**`, quickstarts, install docs | root or owning area | `cd ods && bash tests/test-doc-links.sh`; `cd ods && bash tests/test-install-docs.sh` when install instructions changed | `make smoke` for support/platform claim edits | Docs-only changes usually do not need fleet unless they alter release/support claims. |
| `ods/docs/RELEASE_VALIDATION.md`, `ods/docs/VALIDATION-MATRIX.md`, `ods/docs/SUPPORT-MATRIX.md`, `ods/docs/PLATFORM-TRUTH-TABLE.md`, `ods/manifest.json`, changelog/version files | testing-and-release | `cd ods && bash scripts/check-release-claims.sh`; `cd ods && python3 scripts/check-version-consistency.py`; `cd ods && python3 scripts/validate-golden-paths.py`; `cd ods && python3 scripts/validate-generated-configs.py` | release receipt review; `scripts/release-gate.sh` if operational claims changed | Release language must cite current evidence and disclose skipped/deferred surfaces. |
| `ods/install.sh`, `install.sh`, `install.ps1`, `ods/install-core.sh`, `ods/installers/**`, platform quickstart/troubleshooting docs | installers-and-platforms | `cd ods && bash tests/contracts/test-installer-contracts.sh`; `cd ods && bash tests/contracts/test-preflight-fixtures.sh`; `cd ods && bash tests/test-linux-install-preflight.sh`; platform smoke script matching the edit | `cd ods && bash scripts/simulate-installers.sh`; distro/VM fleet for release-risk installer changes | Real installers are host-mutating. Prefer dry-run, syntax, contracts, smoke, and simulation first. |
| `ods/installers/lib/detection.sh`, tier maps, backend contracts, `ods/config/backends/**`, `ods/config/model-library.json`, hardware class/gpu DB, model selector scripts | hardware-and-models | `cd ods && bash tests/test-tier-map.sh`; `cd ods && bash tests/test-tier-map-parity.sh`; `cd ods && python3 tests/test-model-library-coverage.py`; `cd ods && python3 tests/test-model-library-verdicts.py`; `cd ods && bash tests/contracts/test-overlay-map-coherence.sh` | matching platform smoke; real GPU/fleet only for runtime claims | CPU/static tests prove catalog/contract consistency, not live accelerator behavior. |
| `ods/docker-compose*.yml`, compose overlays, `ods/scripts/resolve-compose-stack.sh`, extension compose files | services-and-extensions plus hardware-and-models when backend overlays change | `cd ods && bash tests/test-resolve-compose-resilient.sh`; `cd ods && bash tests/contracts/test-overlay-map-coherence.sh`; `cd ods && bash scripts/validate-compose-stack.sh --compose-flags "-f docker-compose.base.yml -f <overlay>"` | GitHub `validate-compose` parity; `make smoke`; Docker/fleet for lifecycle claims | Compose config is safer than `up`, but still depends on Docker Compose availability and env placeholders. |
| `ods/extensions/services/**/manifest.yaml`, extension schema/library/catalog, `audit-extensions.py`, `validate-manifests.sh`, `generate-extensions-catalog.py` | services-and-extensions | `cd ods && python3 scripts/audit-extensions.py --project-dir .`; `cd ods && bash tests/test-extension-audit.sh`; `cd ods && bash scripts/validate-manifests.sh`; `cd ods && bash tests/test-validate-manifests.sh`; catalog freshness command if library catalog changed | `validate-compose` for compose-bearing services | Install PyYAML/jsonschema for strict schema validation. |
| `ods/extensions/services/dashboard-api/**` | dashboard-and-api | `cd ods/extensions/services/dashboard-api && pytest tests/ -q`; `cd ods && python3 -m py_compile extensions/services/dashboard-api/main.py extensions/services/dashboard-api/agent_monitor.py` | GitHub dashboard API workflow; coverage run | API tests may require requirements from the service directory. |
| `ods/extensions/services/dashboard/**` | dashboard-and-api | `cd ods/extensions/services/dashboard && npm ci`; `npm run lint`; `npm run test`; `npm run build` | GitHub dashboard frontend workflow | Node dependency installation is safe but can be time/network heavy. |
| `ods/ods-cli`, `ods/ods-*.sh`, `ods/bin/**`, `ods/lib/**`, completions, host-agent, doctor/support bundle, backup/update/migration scripts | ops-cli-and-host-tools | `cd ods && bash tests/run-bats.sh`; `cd ods && bash tests/test-ods-cli-pipefail-tolerance.sh`; `cd ods && bash tests/test-ods-doctor.sh`; `cd ods && bash tests/test-cli-update-verification.sh`; changed-script `bash -n` | post-install lifecycle tests only when authorized | Keep command tests to help/parser/read-only contracts unless the task requires lifecycle effects. |
| `.env.schema.json`, `.env.example`, generated config contracts, runtime config renderer, `validate-env.sh`, `validate-generated-configs.py`, golden paths | testing-and-release plus owning implementation area | `cd ods && bash tests/test-validate-env.sh`; `cd ods && bash tests/test-generated-config-contracts.sh`; `cd ods && bash tests/test-golden-paths.sh`; `cd ods && python3 scripts/validate-generated-configs.py`; `cd ods && python3 scripts/validate-golden-paths.py` | installer simulation if generated config surfaces changed | `validate-env.sh` requires Bash 4+ and jq; it parses `.env` instead of sourcing it. |
| `.github/workflows/**`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `.gitleaksignore`, security prompt/workflow guards | testing-and-release | reproduce the specific workflow's commands locally when possible; `pre-commit run --all-files`; `gitleaks detect --redact --source .`; `cd ods && bash tests/test-issue-to-pr-security.sh` | full CI replay is not always local; document workflow-only gaps | Root secret scan uses gitleaks CLI in CI; pre-commit has its own gitleaks revision and local hooks. |
| `ods/tests/**` | owning area plus testing-and-release | run the changed test directly first; then run the smallest owner lane it belongs to | `make test` if test harness or shared fixtures changed | A changed test passing alone may not prove the production bug path unless the owner lane also runs. |
| `requirements.txt`, `package.json`, `package-lock.json`, Dockerfiles, dependency lock files | owning service/sub-skill plus testing-and-release | service-specific unit/build lane; `cd ods && python3 scripts/check-dependency-pins.py` when lock/pin data changed | dashboard workflow or compose validation if runtime image changes | Dependency changes are small diffs with release risk; consider release-grade gate when runtime wiring changes. |

## Direct changed-test commands

When a test file changed, run it directly before wider suites:

| Test kind | Command pattern |
|---|---|
| Shell test under `ods/tests/*.sh` | `cd ods && bash tests/<file>.sh` |
| Shell contract under `ods/tests/contracts/*.sh` | `cd ods && bash tests/contracts/<file>.sh` |
| BATS test under `ods/tests/bats-tests/*.bats` | `cd ods && bash tests/run-bats.sh tests/bats-tests/<file>.bats` |
| Python test under `ods/tests/**/*.py` | `cd ods && python3 -m pytest tests/<file>.py -q` when pytest-style, otherwise run the file's documented command |
| PowerShell test under `ods/tests/**/*.ps1` | `cd ods && pwsh ./tests/<file>.ps1` |
| Dashboard API test | `cd ods/extensions/services/dashboard-api && pytest tests/<file>.py -q` |
| Dashboard UI test | `cd ods/extensions/services/dashboard && npm run test -- --run <file>` |

## Native candidate traceability

These native candidates are the stable source-backed checks used by this skill:

- `make lint`, `make test`, `make bats`, `make smoke`, `make simulate`, `make gate` from `ods/Makefile`.
- Installer contracts: `tests/contracts/test-installer-contracts.sh`, `tests/contracts/test-preflight-fixtures.sh`, platform smoke scripts, and `scripts/simulate-installers.sh`.
- Hardware/model contracts: `tests/test-tier-map.sh`, `tests/test-tier-map-parity.sh`, model-library tests, overlay coherence, and llama runtime tunable tests.
- Compose/extensions: `tests/test-resolve-compose-resilient.sh`, `scripts/audit-extensions.py --project-dir .`, `tests/test-extension-audit.sh`, `scripts/validate-manifests.sh`, and `scripts/validate-compose-stack.sh`.
- Dashboard: dashboard API `pytest` tests and dashboard UI `npm run lint/test/build`.
- Ops/CLI: BATS runner, CLI flag/pipefail tests, doctor/support/update/backup tests.
- Env/config/release: `tests/test-validate-env.sh`, `tests/test-generated-config-contracts.sh`, `tests/test-golden-paths.sh`, `scripts/check-release-claims.sh`, version consistency, generated config, dependency pin, and golden path validators.
- Security: root pre-commit hooks, gitleaks CLI workflow, private-key and large-file hooks, ShellCheck error gates, and the installer heredoc backtick guard.

## Escalation rules

Escalate from focused lanes to broad lanes when any of these is true:

- The change alters installer phase ordering, bootstrap, public install URLs, generated config writers, compose stack selection, service manifests used at first install, dashboard/API runtime wiring, model routing, GPU detection, lifecycle commands, or release/support claims.
- Focused lanes pass but the change has user-visible install/runtime risk.
- A release candidate needs a User Green or support-status claim.

Escalation candidates, in increasing cost, are: `make smoke`, `make simulate`, `scripts/release-gate.sh`, `make gate`, `make fleet-distros`, `make fleet-vms`, and finally release-grade real-hardware fleet validation. Mark every fleet or real-hardware lane as expensive and environment-dependent.
