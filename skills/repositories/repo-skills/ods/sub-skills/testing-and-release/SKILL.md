---
name: testing-and-release
description: "Select safe ODS validation lanes, interpret CI and release gates,
  and triage test, smoke, simulation, fleet, and secret-scan results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ODS testing and release sub-skill

Use this sub-skill when an ODS task asks which tests to run, why a GitHub Actions lane failed, how to interpret release-readiness evidence, or how to validate changes to tests, CI, validation scripts, smoke/simulation/fleet harnesses, release claim docs, pre-commit hooks, or secret scanning.

## First moves

1. Identify changed paths and classify them before running broad commands. Prefer focused, source-backed lanes over `make gate` or fleet runs.
2. Run the bundled read-only selector when paths are known:

   ```bash
   python3 sub-skills/testing-and-release/scripts/select_validation_lane.py -- <changed paths>
   ```

   The selector accepts paths relative to either the outer ODS repository root or the inner `ods/` product root. It only prints recommendations; it does not run tests, start Docker, install packages, or edit files.
3. Read [references/test-selection.md](references/test-selection.md) for the lane matrix, Make targets, safety classes, native candidate map, and path-to-test routing.
4. Read [references/ci-and-release.md](references/ci-and-release.md) when interpreting GitHub Actions, release gates, User Green claims, validation receipts, or support-matrix wording.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when a lane fails because of missing dependencies, Docker/fleet constraints, platform skips, secret scan hits, or expensive checks.

## Route here for

- `ods/Makefile`, `ods/tests/`, `ods/scripts/validate*.sh`, `ods/scripts/release-gate.sh`, `ods/scripts/simulate-installers.sh`, or `ods/tests/run-bats.sh` behavior.
- GitHub Actions under `.github/workflows/`, especially lint, dashboard, Linux integration, matrix smoke, compose/env/catalog validation, PowerShell, type-check, and secret-scan lanes.
- Choosing focused validation after changes to installers, hardware/model selection, services/extensions, dashboard/API, operator CLI, env/config schemas, release docs, or tests themselves.
- Interpreting release claims in `docs/RELEASE_VALIDATION.md`, `docs/VALIDATION-MATRIX.md`, support/claim docs, changelog/version files, or release notes.
- Classifying `make lint`, `make test`, `make bats`, `make smoke`, `make simulate`, `make gate`, distro-fleet, Incus VM, post-install validation, and real-hardware fleet costs.

## Route elsewhere

- Installer implementation, phase ordering, and platform-specific install bugs: use `../installers-and-platforms/SKILL.md`; return here for validation lane choice.
- GPU/backend detection, tier maps, model catalogs, and model lifecycle implementation: use `../hardware-and-models/SKILL.md`; return here for tier/model test selection.
- Compose layering, service manifests, extension library, and compose security implementation: use `../services-and-extensions/SKILL.md`; return here for manifest/compose validation lane choice.
- Dashboard API/UI implementation: use `../dashboard-and-api/SKILL.md`; return here for CI/test lane interpretation.
- Operator CLI, host-agent, doctor/support bundle, backup/update/runtime command behavior: use `../ops-cli-and-host-tools/SKILL.md`; return here for focused CLI and release validation.

## Safety rules

- Do not run `make gate`, `scripts/release-gate.sh`, distro fleet, Incus VM fleet, full product install, post-install validation, model downloads, or real-hardware fleet checks by default. Mark them as expensive or host-dependent and get explicit user intent.
- `scripts/validate.sh`, `ods-test.sh`, functional tests, model probes, and lifecycle checks require a running or installed ODS stack. Treat them as post-install/product validation, not cheap source checks.
- Docker Compose validation is safer than `docker compose up`, but it still depends on Docker/Compose availability and may read environment variables. Avoid inventing secrets; use documented CI placeholders or fixtures.
- CI and source-level tests do not prove live GPU, Windows, macOS, or real-hardware runtime behavior. Release claims need matching sanitized evidence receipts.
- Keep runtime advice self-contained. Source paths named in this skill are evidence/provenance; future usage should rely on bundled references, the selector script, and public ODS commands/tests.

## Verification shortlist

For a typical code change, start with the selector and then run only the returned focused lanes. Common safe candidates from an ODS checkout include:

```bash
cd ods
make lint
bash tests/test-doc-links.sh
bash tests/contracts/test-installer-contracts.sh
bash tests/contracts/test-preflight-fixtures.sh
bash tests/test-tier-map.sh
bash tests/test-resolve-compose-resilient.sh
python3 scripts/audit-extensions.py --project-dir .
bash tests/run-bats.sh
```

Escalate to `make smoke`, `make simulate`, `make gate`, fleet, post-install, or real-hardware lanes only when the changed surface and release risk justify the cost.

## Source provenance

This sub-skill distills relative source evidence from `ods/Makefile`, `ods/tests/`, `.github/workflows/`, `ods/docs/TESTING.md`, `ods/docs/RELEASE_VALIDATION.md`, `ods/docs/VALIDATION-MATRIX.md`, `ods/docs/SUPPORT-MATRIX.md`, `ods/docs/PLATFORM-TRUTH-TABLE.md`, `ods/scripts/validate*.sh`, `ods/scripts/release-gate.sh`, `ods/scripts/simulate-installers.sh`, `.pre-commit-config.yaml`, `.gitleaks.toml`, and related validation scripts. Claims here should be refreshed when those files change.
