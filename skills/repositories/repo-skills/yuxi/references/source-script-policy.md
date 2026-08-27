# Source script policy

Generated runtime skills should not auto-run repo-owned helpers that mutate `.env`, pull/tag Docker images, touch release metadata, seed persistent databases, or write to external services. This policy records how Yuxi source helpers were handled.

## Bundled/adapted safe helpers

| Bundled script | Source evidence | Safety policy |
| --- | --- | --- |
| `sub-skills/deployment-and-configuration/scripts/check-runtime-health.sh` | Compose files, Makefile commands, quick-start/deployment docs | Read-only. Lists Compose services, prints `docker compose ps`, bounded logs only with `--logs`, curls health endpoints, never starts/stops/builds services or edits env files. |
| `sub-skills/cli-and-external-integration/scripts/check-cli.sh` | CLI README/docs, CLI tests, live help output | Offline by default. Runs CLI help/config checks. A live remote ping requires an explicit `--remote-url` and temporary HOME. |
| `sub-skills/repo-development/scripts/run-selected-checks.sh` | Backend test runner, backend/CLI/frontend metadata, testing docs | Prints selected commands unless `--run` is passed. Service-required checks require `--with-services`; the script never starts/stops Docker Compose. |

## Reference-only source helpers

| Source helper | Owner | Why it is not bundled as a runnable script | How to use the distilled policy |
| --- | --- | --- | --- |
| Unix/PowerShell init helpers | `deployment-and-configuration` | They prompt for secrets, create/edit environment files, and pull images. | Use deployment/config references to identify required variables and images; ask the user before initialization. |
| Unix/PowerShell image pull helpers | `deployment-and-configuration` | They pull, retag, and remove Docker images using registry mirror assumptions. | Diagnose the exact image/registry failure; do not mirror-pull automatically. |
| Backend user seed helper | `deployment-and-configuration` | It writes persistent database state. | Treat admin/user seeding as a deployment state mutation and confirm before use. |
| Version-bump/release helper | `repo-development` | It rewrites version metadata and release/docs fields and is part of a human release process. | Follow `repo-development` release policy: confirm target version/mode, review the diff, commit before tagging. |
| Langfuse dataset upload helper | `cli-and-external-integration` | It writes external Langfuse dataset state through credentials/network. | Use only when the task explicitly asks for Langfuse dataset/eval setup and credentials are supplied. |
| Live API cleanup helper | `repo-development` | It deletes live test artifacts from a running service. | Use only as an explicit cleanup action for a known test run; never as routine verification. |
| Pytest conftest/helpers | `repo-development` / `agent-runtime` | They are fixture support, not standalone operating scripts. | Use them as evidence for test prerequisites and fixture behavior. |

## General rule for future agents

If a source checkout has a helper not listed here, classify it before running:

1. **Read-only and bounded:** may be adapted or run with normal command review.
2. **Mutates local files/services:** ask for confirmation and preserve diffs/logs.
3. **Writes external services or uses credentials:** require explicit user approval and credential availability.
4. **Starts/stops long-running services:** prefer read-only health checks first; ask before changing service state.
5. **Generated/vendor/fixture-only:** use as evidence, not as a bundled runtime script.
