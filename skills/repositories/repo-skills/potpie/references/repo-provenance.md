# Repo provenance

## Source snapshot

- Repository: `potpie`
- Source branch: `main`
- Source commit: `a341978880b9d4c1b403831931279ccedf6184ae`
- Construction dirty state: source evidence was read from the commit above; the working tree had generated `skills/` artifacts added during skill construction.
- Root package version: `potpie` 2.0.0
- Workspace package versions observed during inspection: `potpie-context-engine` 0.1.0, `potpie-context-core` 0.1.0

## Evidence paths used

Primary package and command evidence:

- `pyproject.toml`
- `README.md`
- `Makefile`
- `potpie/cli/`
- `potpie/daemon/`
- `potpie/context-core/src/potpie_context_core/`
- `potpie/context-engine/src/potpie_context_engine/`

Selected documentation evidence:

- `docs/context-graph/README.md`
- `docs/context-graph/architecture.md`
- `docs/context-graph/cli-flow.md`
- `docs/context-graph/querying.md`
- `docs/context-graph/writing.md`
- `docs/context-graph/skills.md`
- `docs/context-graph/ingestion-nudge.md`
- `docs/context-graph/ontology.md`
- `docs/telemetry/sentry.md`

Selected test evidence:

- `tests/unit/test_cli_bootstrap_status.py`
- `tests/unit/test_cli_install_status.py`
- `tests/unit/test_daemon_launcher.py`
- `tests/unit/test_daemon_rpc.py`
- `tests/unit/test_ui_router.py`
- `tests/unit/test_telemetry_cli.py`
- `tests/unit/test_pot_create_repo.py`
- `tests/unit/test_source_cli_contract.py`
- `tests/unit/test_repo_location.py`
- `tests/unit/test_setup_first_pot.py`
- `tests/unit/test_empty_pot_guidance.py`
- `tests/unit/test_cli_gitlab.py`
- `tests/unit/test_cli_linear.py`
- `tests/unit/test_github_cli_auth.py`
- `tests/unit/test_cli_atlassian.py`
- `tests/unit/test_gitbucket_cli.py`
- `tests/unit/test_potpie_auth_helpers.py`
- `tests/unit/test_graph_cli_contract.py`
- `tests/unit/test_skills_cli.py`
- `tests/unit/test_setup_agent_skills.py`
- `tests/unit/test_setup_defer_skills.py`
- `tests/unit/test_repo_baseline_skill.py`
- `potpie/context-core/tests/unit/`
- `potpie/context-engine/tests/unit/`

Bundled/adapted source scripts:

- `scripts/typecheck_public_context_api.py` -> `scripts/typecheck_public_context_api.py`
- `potpie/context-engine/scripts/generate_agent_contract.py` -> `scripts/generate_agent_contract.py`

Explicitly excluded from this skill's operating scope:

- `potpie/parsing/`
- `potpie/sandbox/`
- `potpie/integrations/`
- sandbox/planning/debug handoff documents
- benchmark/lab scripts under `potpie/context-engine/scripts/`
- live credentialed provider e2e tests
- cloud/managed roadmap command implementation paths

## Installed-package facts used

- CLI entry points: `potpie` and `potpie-daemon`.
- Default host mode: `daemon`.
- Default backend profile: `falkordb_lite`.
- Public command groups observed: runtime/setup/status/doctor, pot/source, auth/provider groups, ledger, graph, timeline, backend, skills, telemetry, and UI.
- Bundle skill IDs observed: `potpie-change-timeline`, `potpie-cli`, `potpie-debug-memory`, `potpie-graph`, `potpie-infra-architecture`, `potpie-project-preferences`, `potpie-repo-baseline`, `potpie-source-ingestion`.
- The selected scope does not require accelerator backend verification.

## Staleness triggers

Refresh this skill if any of these change:

- `pyproject.toml` package metadata or entry points.
- `potpie/cli/commands/` command names, options, or output contracts.
- `docs/context-graph/` command or graph contract documentation.
- `potpie/context-core` graph schema, context records, or mutation DSL.
- `potpie/context-engine` skill manager, bundle catalog, graph workbench, or backend profiles.
- The packaged bundle under `potpie.cli` templates.
- Provider auth flows or external Event Ledger behavior.
