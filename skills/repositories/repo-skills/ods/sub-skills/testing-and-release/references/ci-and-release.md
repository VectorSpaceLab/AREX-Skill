# ODS CI and release validation reference

This reference explains how to read ODS CI lanes and release-readiness claims. It distills the public workflow files, validation docs, release-claim scripts, and support matrix rules. Do not treat CI logs or private fleet artifacts as runtime dependencies; use the rules below to decide what evidence is required.

## GitHub Actions map

| Workflow | Trigger / path focus | Main checks | Local reproduction guidance |
|---|---|---|---|
| `lint-shell.yml` | pushes/PRs | ShellCheck over `ods/` shell scripts, reports warnings, fails error-severity issues; regression guard forbids `curl http://localhost:` in shell scripts except documented exclusions | `cd ods && make lint` for syntax; run ShellCheck with the workflow's excluded codes/severity when diagnosing CI-only failures |
| `lint-python.yml` | pushes/PRs | Ruff over `ods/` Python files with `E,F,W` selected and selected ignores | `ruff check ods/ --select E,F,W --ignore E501,E701,E731,E741,E402` |
| `type-check-python.yml` | Python path changes | mypy over dashboard-api, token-spy, privacy-shield, and scripts; steps are `continue-on-error` | reproduce only for the changed service; treat failures as signal even when CI does not hard-fail |
| `lint-powershell.yml` | pushes/PRs on Ubuntu and Windows | Installs PSScriptAnalyzer, scans installer PowerShell plus root `install.ps1`, then runs Windows contract tests | Use `pwsh` and `PSScriptAnalyzerSettings.psd1`; Windows-only footprint tests require a Windows runner |
| `dashboard.yml` | pushes/PRs | Dashboard frontend `npm ci`, lint, tests, build; dashboard API py_compile, requirements install, pytest with coverage | Run commands in the service directory that changed |
| `test-linux.yml` | pushes/PRs | Token-spy Postgres test plus broad Linux integration-smoke: docs links, install docs, fleet lock, integration smoke, extension audit/runtime checks, BATS, tier map, service registry, manifest/env/golden/config tests, installer simulation, update rollback, support bundle, issue-to-PR security, and artifact upload | Reproduce the failing step rather than the whole workflow. Many commands are listed in `references/test-selection.md`. |
| `matrix-smoke.yml` | pushes/PRs | Linux smoke scripts; 10-container distro matrix for package-manager detection, `pkg_install`, and installer syntax; macOS dispatch smoke and Bash 3.2 syntax checks | Run the matching smoke script locally first. Multi-distro behavior maps to `tests/fleet-multi-distro.sh` for a fuller local lane. |
| `validate-compose.yml` | compose/resolver path changes | Docker Compose config for base, installer overlays, GPU overlays, multi-GPU overlays, and AMD multi-GPU resolver output | Use `docker compose ... config --quiet` or `scripts/validate-compose-stack.sh --compose-flags ...` with CI placeholder env values as needed |
| `validate-env.yml` | pushes/PRs | Generates tier 0-4 fixture `.env` files and validates them against `.env.schema.json` with `scripts/validate-env.sh` | Run `cd ods && bash tests/test-validate-env.sh` for validator behavior and targeted fixture checks |
| `validate-catalog.yml` | extension catalog path changes | Regenerates `ods/config/extensions-catalog.json` from library manifests and diffs ignoring `generated_at` | `python ods/scripts/generate-extensions-catalog.py` then compare generated catalog without timestamp |
| `secret-scan.yml` | pushes/PRs | Installs OSS gitleaks CLI, runs `gitleaks detect --redact --verbose --source .`, uploads redacted JSON report | `gitleaks detect --redact --source .`; inspect `.gitleaks.toml` allowlist before suppressing findings |
| `release-notes.yml` | release creation or manual dispatch | Optional AI release notes generation when a release-note API secret is configured | Not a validation lane for source correctness; use release docs and claim checks for readiness assertions |

## CI triage workflow

1. **Start from the failing job and step name.** Map it to the workflow row above and the owning sub-skill. Do not rerun the entire matrix until the failing step is understood.
2. **Reproduce the exact command where possible.** CI often runs from the inner `ods/` directory; preserve that working directory.
3. **Classify environment-sensitive failures.** Docker daemon, Incus, macOS Bash 3.2, PowerShell, Node, Python requirements, gitleaks installation, and network package-manager issues can be lane prerequisites rather than product regressions.
4. **If a workflow changed, test the commands it contains.** A YAML syntax or action pin change may need GitHub-side confirmation that cannot be fully reproduced locally.
5. **Route implementation bugs to the owning sub-skill.** This sub-skill chooses and interprets validation lanes; it does not own installer, hardware/model, extension, dashboard, or CLI implementation facts.

## Release gates and what they prove

ODS release validation is appliance-oriented. A source test pass is not enough for a release claim when the diff affects install/runtime behavior.

| Gate | Required meaning |
|---|---|
| Zero-prereq bootstrap | Clean distro containers can fetch the public installer and provision missing prerequisites such as Git, Python, Docker, and Compose. |
| Install Green | Enabled real-hardware hosts can fresh-install from the public bootstrap path. |
| Product Green | Core services, cloud contracts, dashboard flows, Hermes auth/chat, and UI checks pass after install. |
| Capability Green | Full-model capability probes pass after large model downloads/swaps, or deferrals are explicit. |
| Model Switchboard Green | Model-management release coverage proves the planned distinct-model cycles and app probes on reachable hosts. |
| Lifecycle Green | Idempotent reinstall, `ods restart`, and `ods doctor` recover after state changes. |
| User Green | The combined release gate is clean, with failures, skips, and deferrals resolved or documented. |

Release-grade validation combines four layers: CI, zero-prereq bootstrap containers, a distro lab with Docker containers and Incus VMs, and a real-hardware fleet covering enabled Linux NVIDIA, Linux AMD/ROCm-Lemonade, ARM Linux NVIDIA, Apple Silicon, and optional Windows targets. Containers and CI are breadth and regression checks; physical machines remain the release gate for accelerator and installed-product behavior.

## Release-check scripts

`ods/scripts/release-gate.sh` runs a release checklist independent of the Makefile's `gate` target:

1. shell syntax over tracked shell files;
2. compatibility and claims: `check-compatibility.sh`, `check-version-consistency.py`, `check-release-claims.sh`, `validate-golden-paths.py`, `validate-generated-configs.py`, and `check-dependency-pins.py`;
3. selected contracts, including install docs, hosted bootstrap verifier, installer/preflight/hardening, uninstall flags, Windows missing service hints, and network/remote-provider contracts;
4. smoke scripts for Linux AMD, Linux NVIDIA, WSL, and macOS dispatch;
5. installer simulation and simulation summary validation;
6. update rollback contract.

Use it when a release checklist is requested or when operational claims changed. For ordinary development, use focused lanes first.

## Release evidence receipt

Before a release is described as ready, the public release notes or validation summary should cite a sanitized receipt with:

- ODS version and matching tag or release candidate;
- commit or product SHA under test;
- run date;
- sanitized hardware classes covered;
- distro lab breadth and regression replay result;
- install, verify, dashboard, Hermes, UI, capability, and lifecycle summaries;
- skipped, deferred, blocked-by-environment, or not-run phases;
- known gaps that should not be read as supported behavior.

Never publish raw private fleet logs, hostnames, LAN addresses, usernames, local filesystem paths, or unredacted secrets. Public docs should quote the sanitized evidence.

## Support and claim guardrails

- Linux, Windows Docker Desktop + WSL2, and macOS Apple Silicon have supported installer/runtime paths, but release-current evidence must name which hardware classes actually ran.
- Windows evidence is release-relevant only when the Windows target produces candidate-specific preflight, install, verify, dashboard, and UI artifacts.
- Intel Arc is experimental unless a release cites a successful Arc fleet run for the candidate and specific hardware.
- macOS does not imply full Linux runtime parity; GPU image-generation surfaces and optional modes require their own evidence.
- ODS Talk, owner-card, vision, AP mode, LAN, router, Wi-Fi, mDNS, and client-device behavior are target-mode validations, not default source-test results.
- A green release fleet pass is strong release evidence, not a long-term soak, thermal, benchmark, or unsupported-driver guarantee.

## Secret scan and pre-commit semantics

Root pre-commit hooks include:

- gitleaks;
- private-key detection;
- large-file checks capped at 500 KB;
- ShellCheck over installer/script shell surfaces at error severity;
- an explicit SC2006 regression guard for legacy backticks;
- a local heredoc backtick guard for unquoted heredoc bodies under installer/scripts surfaces.

Root gitleaks configuration adds Langfuse key patterns and allowlists installer key-generation templates that are not real secrets. If a scan fails, prefer removing or redacting the value. Only adjust allowlists when the finding is a documented non-secret template, and rerun both pre-commit and the gitleaks CLI lane.

## Reading release failures

- **Missing ledger or fewer than planned distinct model cycles:** User Green must fail or be deferred; do not reinterpret as pass.
- **Open WebUI returns 401/login wall for a required probe:** record failed or deferred auth blocker; unauthenticated health does not prove model viability.
- **Capability probes deferred during download/swap:** watcher must rerun and update the report before User Green can pass.
- **Incus Arch/openSUSE nested Docker failures:** separate lab limitations from product regressions using container lanes and real-hardware evidence.
- **Release claim wording changed:** run `check-release-claims.sh`, verify version consistency, and ensure the receipt names current evidence.
