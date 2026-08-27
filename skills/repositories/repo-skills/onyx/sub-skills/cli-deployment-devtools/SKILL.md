---
name: cli-deployment-devtools
description: "Onyx CLI, developer tooling, Docker Compose, Helm, local services,
  migrations, and release tooling guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI Deployment Devtools

Use this sub-skill when work involves the Onyx product CLI, the `ods` developer utility, local service orchestration, Docker Compose or Helm deployment, migration/run commands, or dev/release automation.

Keep the boundaries clear: `onyx-cli` is the user/product CLI for querying Onyx and managing guided self-hosted installs, while `ods` is the repository developer tool for composing services, running local backends, generating artifacts, and operating contributor workflows.

Require explicit user approval before destructive host, deployment, remote GitHub, or database actions such as deploy uninstall, compose down on a shared stack, forced recreate, DB drop/restore/downgrade, Helm uninstall, release tagging, or queueing/closing PRs.

Route implementation internals to sibling skills: backend APIs, Celery, migrations, SQLAlchemy, or backend tests to `backend-platform`; web UI/Bun internals to `web-frontend`; mobile app issues outside this sub-skill.

Read [references/onyx-cli.md](references/onyx-cli.md) when you need install/config details, non-interactive conventions, ask/search/image commands, deployment lifecycle commands, SSH serving, skill installation, exit codes, or CLI-specific troubleshooting.

Read [references/ods-devtools.md](references/ods-devtools.md) when you need `ods` command workflows for compose, logs, pull, backend, web, DB, OpenAPI, lazy imports, audit, CI, cherry-pick, screenshot diff, trace, devcontainer, generate-compose, or release tooling.

Read [references/deployment-workflows.md](references/deployment-workflows.md) when you need local development setup, Docker Compose standard/lite/Craft deployment patterns, Helm/Kubernetes high-level guidance, environment template handling, migrations, generated-compose rules, or safe DB/log access.

Read [references/troubleshooting.md](references/troubleshooting.md) when missing Docker, Compose, Bun, Go, uv, GitHub CLI, AWS, DHI access, image pulls, environment/secrets, Postgres access, merge queue, Dependabot, or generated-compose drift is the likely blocker.
