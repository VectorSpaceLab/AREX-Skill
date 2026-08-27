# Repository scripts and release/compliance tooling

This reference distills Make targets, development scripts, release tooling, and script safety guidance. It intentionally summarizes script behavior rather than copying source code.

## Script safety levels

Before running any repository script, classify it:

| Safety level | Meaning | Rule |
| --- | --- | --- |
| Read-only inspection | Reads files and exits with status/report | Safe to run during triage; still inspect output for warnings. |
| Deterministic code generation | Rewrites known generated files | Prefer official Make target or script; inspect diff; run associated sync test. |
| Local mutable dev data | Writes to local running stack or local files | Use only on disposable/local environments; never against production by accident. |
| Network snapshot/compliance | Downloads or queries external data | Confirm the source, need, and reproducibility; inspect generated files. |
| Release automation | Changes version files, changelog, release notes, manifest, branches, PRs | Run preview first; requires clean `main`, authenticated GitHub CLI, and human confirmation. |
| Destructive stack operation | Deletes volumes or resets local state | Confirm user intent before running. |

Prefer preview or dry-run modes when available. Never run live-data seeders, backfills, release creation, or destructive stack targets merely to gather evidence.

## Make targets as the stable entrypoints

| Target | Purpose | Safety notes |
| --- | --- | --- |
| `help` | Show documented Make targets | Read-only. |
| `lint` | Ruff check over repository Python | Read-only except cache files. |
| `format` | Ruff format and auto-fix | Mutates source; inspect diff. |
| `check` | Pre-commit over all files | May mutate staged SPDX headers via hook; inspect diff. |
| `test`, `test-v` | Root Python test suite from server context | Read-only/hermetic by design. |
| `test-adversarial` | BenchJack self-test suite | Read-only test run. |
| `test-eval-completeness` | Eval completeness tests | Read-only test run. |
| `test-fuzz` | OSS-Fuzz target smoke tests | Needs fuzz dependency; read-only test run. |
| `test-all` | Root, eval, and adversarial tests | Broad test run. |
| `sync-skill` | Regenerate bundled Observal command reference | Mutates generated skill reference when CLI command surface changed. |
| `hooks` | Install pre-commit, commit-msg, and pre-push hooks | Local Git config mutation only. |
| `up`, `down`, `logs` | Start/stop/tail Docker stack | Local stack only. |
| `rebuild-fast` | Rebuild API/web images and restart stack | Normal rebuild for app and dependency changes. |
| `rebuild` | Full compose rebuild and restart | Use for topology/image/volume/network changes. |
| `rebuild-clean` | No-cache rebuild and volume removal | Destructive; use only after confirmation. |
| `reset` and observability reset variants | Delete volumes and rebuild | Destructive. |
| `migrate` | Run PostgreSQL migrations in local stack | Requires running stack. |
| `migrate-clickhouse` | Run ClickHouse migrations via service module | Requires local stack context. |
| `check-migrations` | Validate Alembic chain | Read-only. |
| `new-migration` | Generate Alembic revision with `MSG` | Mutates migration directory; inspect generated file. |
| `release-preview` | Render curated release preview | No branch/PR creation. |
| `release` | Interactive release PR preparation | Mutates release files in worktree/branch after human confirmation. |

## Development, sync, and quality scripts

| Script | Use | Expected signal | Safety notes |
| --- | --- | --- | --- |
| `scripts/check_migrations.py` | Validate Alembic revision IDs, heads, down-revisions, and linear chain | Prints `Migration chain OK: ...` and exits 0 | Read-only; run after migration changes. |
| `scripts/check_secrets.sh` | Pre-commit guard for staged `.env` files and common secret patterns | No errors; exits 0 | Reads staged diff; do not bypass unless a maintainer explicitly approves. |
| `scripts/update_spdx_copyright.py` | Pre-commit hook adding committer SPDX copyright lines to staged files with headers | Staged files updated if needed | Mutates files; inspect diff. |
| `scripts/add_spdx_headers.py` | Broad repair that adds SPDX headers from git history and REUSE metadata | Headers/REUSE data updated | Mutates many files; use only for dedicated license repair. |
| `scripts/sync_observal_skill.py` | Regenerate auto-generated command reference block in bundled Observal skill | Prints already-in-sync or regenerated message | Run via `make sync-skill` after CLI surface changes; associated sync tests should pass. |
| `scripts/sync_features.py` | Generate web feature registry from Python feature registry | Prints generated feature count | Mutates frontend feature file; run when feature registry changes. |
| `scripts/check_terraform_consistency.py` | Compare Terraform modules, app env vars, injected secrets, and `.env.example` coverage | PASS, PASSED with warnings, or FAILED summary | Read-only; warnings may be non-blocking but must be reported. |

## Compliance, license, SBOM, and vulnerability scripts

| Script | Use | Expected signal | Safety notes |
| --- | --- | --- | --- |
| `scripts/check_license_policy.py` | Check ScanCode JSON output for prohibited/restricted licenses | Exits 0 if no policy violations | Requires an existing scan result file; read-only on repo. |
| `scripts/generate_third_party_notices.py` | Generate third-party notices from Python and Node dependency license metadata | Notice file regenerated | Calls package tooling; inspect generated notices and dependency provenance. |
| `scripts/generate_vex.py` | Generate timestamped OpenVEX document from static VEX statements | Prints generated output path and statement count | Mutates output file; timestamp changes by design. |
| `scripts/check_vulnerabilities.py` | Query VulnerableCode for CycloneDX SBOM components | Reports vulnerability findings from API response | Network access; not deterministic if service data changes. |

Use compliance scripts when the change introduces, removes, or updates dependencies, artifacts, release metadata, license policy, SBOM/VEX evidence, or security packaging claims. Do not run network vulnerability checks as a routine lint substitute.

## Model/catalog and harness snapshot scripts

| Script | Use | Expected signal | Safety notes |
| --- | --- | --- | --- |
| `scripts/refresh_harness_models.py` | Refresh vendored harness model catalogs | Generated catalog files and metadata | Network access; route detailed harness impact to `harness-telemetry`. |
| `scripts/refresh_litellm_model_snapshot.py` | Refresh vendored LiteLLM model catalog snapshot | Model catalog JSON regenerated | Network access; route server-side LiteLLM behavior to `server`. |
| `scripts/backfill_harness_telemetry.py` | One-shot ClickHouse telemetry rename/backfill | Completes async migration call | Live data mutation; only use under an explicit migration/backfill plan. |

## Local seeding, live verification, and E2E scripts

| Script | Use | Expected signal | Safety notes |
| --- | --- | --- | --- |
| `scripts/seed_exec_dashboard.py` | Seed exec dashboard test data into PostgreSQL and ClickHouse | Seeded rows/users/sessions reported | Mutates a live database; use only on local or disposable environments. |
| `scripts/seed_insight_report.py` | Seed a completed insight report for self-learn testing | Report and suggestions created | Contains container/local assumptions; treat as local dev only. |
| `scripts/seed_test_skill.py` | Seed a test skill into a local Observal instance | Login/submission/approval/install steps print progress | Uses local demo credentials and live API; never use against production. |
| `scripts/verify_exec_dashboard.py` | Verify exec dashboard endpoints against a reachable deployment | Endpoint checks pass or report failures | Requires base URL and JWT; do not expose tokens in logs or shell history. |
| `scripts/test_version_e2e.sh` | Full CLI version/update E2E mechanics | Prints pass sections and exits 0 | Live E2E script; validate environment and avoid production side effects. |
| `scripts/test_xff_spoofing.sh` | Verify X-Forwarded-For spoofing cannot bypass login rate limiting | Requests past limit return 429 after fix | Requires running stack; security-sensitive evidence should be shared responsibly. |

Local seeders are not substitutes for unit tests. Use them to demonstrate a manual workflow only after focused tests cover behavior.

## Release tooling

Primary commands:

```bash
make release-preview
make release
uv run python tools/release.py --preview
uv run python tools/release.py
```

Release preflight expects:

- Clean working tree.
- Current branch is `main`.
- Local `main` exactly matches the configured upstream `main` after fetch.
- `git`, `gh`, and `uv` are available.
- GitHub CLI authentication succeeds.
- Stable release tags and the release manifest can be resolved.

Release flow distilled from the tool:

1. Fetch upstream `main` and tags.
2. Locate the previous stable tag and release cutoff.
3. Discover contiguous changes since the previous cutoff.
4. Ask the human to choose the cutoff, release-note entries, categories, highlights, breaking-change state, version bump, and channel.
5. Refuse to omit database migrations from release notes.
6. Render changelog and release notes preview.
7. In preview mode, stop before branch/PR creation.
8. In full mode, create a release branch/worktree, update version files and locks, prepend changelog, update release notes, write the release manifest, commit, push, and open a PR.
9. Ensure only expected release files changed.

Use preview for planning and review. Use full release only with explicit human confirmation and appropriate permissions.

## Release artifact verification summary

When verifying downloaded release artifacts, checksum verification alone is not proof of origin. The release process expects both:

- SHA-256 checksum verification of downloaded bytes.
- GitHub keyless Sigstore provenance attestation verification against the release workflow identity.
- For signed tags, gitsign verification of the release tag against the same GitHub Actions workflow identity and OIDC issuer.

A signed tag does not replace artifact provenance verification; use both when source commit and exact bytes matter.

## Safe script-use checklist

Before running a script, answer:

- Does it write files, stage files, alter a database, call Docker, call the network, push a branch, or open a PR?
- Is there a Make target wrapper or preview mode?
- Is the environment local/disposable, or could this reach production?
- Are credentials, tokens, demo passwords, or live telemetry involved?
- Which output or diff will prove success?
- Which owning sub-skill should review the domain-specific effect?

After running a script, report:

- Exact command.
- Exit status and key success/failure line.
- Files changed, generated, or intentionally untouched.
- Any warnings, nondeterministic network data, or environment assumptions.
