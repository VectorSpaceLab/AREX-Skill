# ODS Developer Tools

`ods` is the repository developer utility distributed as `onyx-devtools`. Use it for local service orchestration, repo artifact generation, contributor workflows, and release/dependency maintenance. It is not the same as `onyx-cli`; use [onyx-cli.md](onyx-cli.md) for product CLI and guided self-hosted deployment commands.

## Setup and prerequisites

In a normal Onyx checkout, `ods` is available from the project Python environment after dependencies are synced. If it is missing, install the `onyx-devtools` package or build the tool only when Go 1.24+ is available.

External tools are command-dependent:

| Tool | Needed for |
| --- | --- |
| Docker with Compose | `ods compose`, `ods logs`, `ods pull`, and many DB/container helpers. |
| `uv` | `ods backend`, OpenAPI generation, backend-oriented Python commands, and package builds. |
| Bun | `ods web`, frontend dependency setup, devcontainer CLI installation, and some release/dependabot repairs. |
| GitHub CLI (`gh`) | `ods run-ci`, `ods cherry-pick`, `ods trace`, and GitHub-backed diagnostics. Authenticate before remote operations. |
| AWS CLI/credentials | `ods screenshot-diff` S3 operations, audit allowlist uploads/downloads, and seeded DB snapshot fetches. |
| devcontainer CLI | `ods dev`/`ods dc` commands. |
| Go 1.24+ | Native `ods`/`onyx-cli` builds and Go tests; optional for most Python/TypeScript work. |

Global flags:

```bash
ods --debug <command>
ods --project <compose-project> <command>
```

`--project` sets the Docker Compose project name for commands that operate on containers. Use it when multiple stacks may be running.

## Docker Compose orchestration

Start or stop repository Docker Compose services:

```bash
ods compose
ods compose dev
ods compose multitenant
ods compose --tag edge
ods compose --wait=false
ods compose --force-recreate
ods compose dev --infra
ods compose --down
```

Profiles:

| Profile | Compose behavior |
| --- | --- |
| default | Standard `docker-compose.yml`; Enterprise Edition features enabled by default for development. |
| `dev` | Adds dev overlay, exposes service ports, and activates the S3 filestore profile for MinIO. |
| `multitenant` | Uses the multitenant dev compose file. |

Important flags:

| Flag | Effect |
| --- | --- |
| `--down` | Runs compose down for the chosen profile. Confirm before stopping a shared stack. |
| `--wait` | Waits for service health on startup; defaults to true. |
| `--force-recreate` | Recreates containers even if unchanged. Confirm before using on a shared or long-running stack. |
| `--tag <tag>` | Sets `IMAGE_TAG` for compose. |
| `--no-ee` | Disables Enterprise Edition features; default enables EE and disables license enforcement for development. |
| `--infra` | Starts or stops only infrastructure services such as database, cache, search, and model servers. |

View container logs:

```bash
ods logs
ods logs api_server
ods logs api_server background
ods logs --tail 100 api_server
ods logs --follow=false
```

`ods logs` follows by default; use `--follow=false` for bounded agent output. Logs can include secrets, tokens, prompts, or document content; scope services and tail windows.

Pull images:

```bash
ods pull
ods pull --tag edge
```

Image pulls require Docker registry access. If building locally rather than pulling published images, see the DHI and image-pull notes in [troubleshooting.md](troubleshooting.md).

## Backend and web runners

Run backend services with environment loaded from the repo developer `.env` file. On first use, `ods backend` creates that file from the repo template if needed. Shell environment variables take precedence over file values.

```bash
ods backend api
ods backend api --port 9090
ods backend api --no-ee
ods backend model_server
ods backend model_server --port 9001
```

Defaults:

- `api` runs the FastAPI app with hot reload on port 8080 unless `--port` changes it.
- `model_server` runs the model server with hot reload on port 9000 unless `--port` changes it.
- EE is enabled by default with license enforcement disabled; use `--no-ee` only when you intentionally need Community Edition behavior.

Run frontend package scripts from the repository root without manually changing directories:

```bash
ods web dev
ods web lint
ods web test --watch
```

`ods web <script> [args...]` forwards the script and arguments to Bun using script names from the frontend package manifest. Use the web-focused sibling skill for component, route, or test implementation details.

## Database and migration workflows

Read-only or low-risk DB inspection:

```bash
ods db current
ods db current --schema private
ods db history
ods db history --verbose
ods db dump snapshot.dump
ods db dump snapshot.sql --format sql
```

Migration commands:

```bash
ods db upgrade
ods db upgrade head
ods db upgrade +1
ods db upgrade --schema private
```

`ods db upgrade` runs Alembic migrations and auto-detects the PostgreSQL container IP when `POSTGRES_HOST` is not set. Supported DB env variables include `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.

Destructive commands require explicit approval and a clear target database/schema:

```bash
ods db downgrade -1
ods db restore snapshot.dump
ods db restore snapshot.dump --clean
ods db restore --fetch-seeded
ods db drop
ods db drop --schema schema_name
```

Safety notes:

- `downgrade` rolls schema state back and can break a running app; confirm the revision and backup state.
- `restore` may overwrite existing data; `--clean` drops objects before restore.
- `restore --fetch-seeded` downloads a seeded dump from S3 and requires network/AWS access.
- `drop` drops/recreates the database or schema; it prompts unless `--yes` is passed. Do not use `--yes` without explicit user approval.

For backend model changes, migration authoring, and test selection, route to `backend-platform`.

## OpenAPI and lazy imports

Generate API schema and client artifacts:

```bash
ods openapi schema
ods openapi schema -o api.json
ods openapi client
ods openapi all
ods openapi all --client-output generated-client
```

Requirements include a backend-capable Python environment; client generation also needs the OpenAPI generator dependency available through the tool environment.

Check lazy import compliance:

```bash
ods check-lazy-imports
ods check-lazy-imports onyx/llm/
ods check-lazy-imports onyx/chat/chat.py
```

The lazy-import check scans backend Python files for modules that must not be imported at module import time. It exits non-zero and prints offending lines when violations are found.

## Security audit workflow

Audit lockfiles and Dependabot security alerts:

```bash
ods audit
ods audit --python
ods audit --web
ods audit --actions
ods audit --dependabot
ods audit --format=sarif,text > audit.sarif
ods audit --fail-on high
```

With no selector flags, all supported sources are audited. Human-readable text is written to stderr when combined with a machine-readable format so stdout can remain JSON/SARIF. The command exits non-zero when an unignored finding at or above the severity gate remains.

Manage advisory suppressions only after assessment:

```bash
ods audit ignore
ods audit ignore add GHSA-xxxx-xxxx-xxxx --ecosystem npm \
  --reason "not reachable in our usage" --expires 2026-09-01
```

Suppression writes/upload affect deploy gates; require review context and approval before `--yes` or any S3-backed allowlist update.

## CI, cherry-pick, and GitHub operations

`run-ci` creates or updates a main-repo branch/PR to run Actions for a fork PR:

```bash
ods run-ci 7353 --dry-run
ods run-ci 7353
ods run-ci 7353 --rerun
```

Flags include `--dry-run`, `--yes`, `--rerun`, and `--no-verify`. Pushing branches and creating PRs are remote side effects; confirm before running without `--dry-run`.

`cherry-pick` backports commits or PRs to release branches:

```bash
ods cherry-pick abc123 --release 2.5 --dry-run
ods cherry-pick abc123 def456 --release 2.5 --release 2.6
ods cherry-pick <pr-number> --release 2.5
ods cherry-pick --continue
ods cherry-pick abc123 --dispatch
```

Flags include `--release`, `--assignee`, `--dry-run`, `--yes`, `--no-verify`, `--continue`, and `--dispatch`. Backports create commits/branches/PRs; confirm target releases and conflict-handling before side effects.

## Screenshot diff and Playwright traces

Compare screenshots against baselines:

```bash
ods screenshot-diff compare --project admin
ods screenshot-diff compare --project admin --rev release/2.5
ods screenshot-diff compare --project admin --from-rev v1.0.0 --to-rev v2.0.0
ods screenshot-diff compare --baseline baselines --current web/output/screenshots --output report/index.html
```

Upload baselines:

```bash
ods screenshot-diff upload-baselines --project admin
ods screenshot-diff upload-baselines --project admin --rev release/2.5
ods screenshot-diff upload-baselines --project admin --delete
```

Compare writes a `summary.json` beside the report and generates HTML only when visual differences are detected. Upload/delete operations affect S3 baselines; require explicit approval.

Download and inspect CI Playwright traces:

```bash
ods trace
ods trace 12345678
ods trace --pr 9500
ods trace --branch main
ods trace --project admin
ods trace --list
ods trace --no-open
```

`trace` uses GitHub Actions artifacts and a local temp cache. It can list traces without opening them for non-GUI environments.

## Devcontainer commands

Manage the published Onyx devcontainer image:

```bash
ods dev up
ods dev into
ods dev exec -- bun test
ods dev restart
ods dev rebuild
ods dev stop
ods dev tunnel 3000
```

The alias `ods dc` supports the same subcommands. `restart`, `rebuild`, and `stop` alter running containers; confirm if a user may have active work inside.

## Generated compose and release tooling

Regenerate generated Docker Compose outputs after changing the shared compose template or embedded deployment files:

```bash
ods generate-compose
ods generate-compose --write
```

Without `--write`, the command acts as a check. With `--write`, it rewrites generated compose variants and refreshed embedded guided-install copies; include those changes together.

Release/package notes:

```bash
# CLI release tags use the cli/ prefix; ods release tags use the ods/ prefix.
tag --prefix cli
tag --prefix ods

# Wheel builds use uv and cross-compile Go binaries when Go is available.
uv build --wheel
```

Creating tags, publishing packages, pushing release branches, or triggering release workflows are remote/release side effects. Require user approval and confirm the intended version before acting.
