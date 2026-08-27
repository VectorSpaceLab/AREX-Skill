# CLI, Deployment, and Devtools Troubleshooting

Use this reference when a CLI/devtools/deployment workflow is blocked by missing tools, auth, images, environment files, database access, generated files, or GitHub workflow caveats. Prefer read-only probes first and ask for approval before destructive or remote side effects.

## Quick read-only probes

```bash
command -v onyx-cli || true
command -v ods || true
command -v docker || true
docker version
docker compose version
command -v uv || true
command -v bun || true
command -v go || true
command -v gh || true
gh auth status
command -v aws || true
aws sts get-caller-identity
```

Only run commands that make sense for the task. Some probes contact external services (`gh auth status`, AWS identity) and may fail when credentials are intentionally absent.

## Docker and Compose

Symptoms:

- `docker: command not found`
- `Cannot connect to the Docker daemon`
- `docker compose version` fails
- Compose up waits forever or marks services unhealthy
- Rootless/WSL Docker behaves differently from Docker Desktop

Recovery:

1. Confirm Docker is installed and the daemon is running.
2. Confirm the Compose plugin works with `docker compose version`.
3. Use bounded logs while debugging startup:

   ```bash
   ods logs --follow=false --tail 100 api_server
   onyx-cli deploy status --json
   onyx-cli deploy logs api_server --tail 200
   ```

4. For `onyx-cli deploy install` on Linux/WSL, the CLI can offer Docker Engine/Compose plugin installation after confirmation. Do not accept host package installation without explicit user approval.
5. If ports conflict in dev mode, prefer `ods compose dev` because it writes available host ports into the local compose `.env`; otherwise choose explicit host ports.

## Image pulls, offline mode, and DHI login

Published image pulls for normal Compose startup use public Onyx images. Local image builds can be different:

- Building the web image and model-server image may pull Docker Hardened Images from `dhi.io`.
- If a build fails with DHI auth errors, run Docker login only after confirming the user has access:

  ```bash
  docker login dhi.io
  ```

- `onyx-cli deploy install --offline` and `onyx-cli deploy upgrade --offline` promise no network access. They require local deployment files and already-loaded images. If images are missing, load them first or re-run without `--offline` after approval.
- Floating tags such as `latest` may trigger pulls/recreates. Pin `--tag vX.Y.Z` when reproducibility matters.

## uv and Python environment

Symptoms:

- `uv: command not found`
- `ods backend` cannot launch `uvicorn`
- OpenAPI generation cannot import backend modules
- CLI/ods wheel build fails

Recovery:

```bash
uv venv .venv --python 3.13
uv sync
uv run playwright install
```

Use Python 3.13 for the project environment. Python 3.14 is not supported by all dependencies. For backend route/migration/test problems, route to `backend-platform`.

## Bun and frontend tooling

Symptoms:

- `bun: command not found`
- `ods web dev` or `ods web lint` fails before running the script
- Frontend lockfile or generated output is stale

Recovery:

```bash
cd web
bun install
bunx oxlint
bunx oxfmt .
cd -
```

For UI implementation or frontend test failures, route to `web-frontend`. For Dependabot JavaScript lockfile repair, see the merge queue/Dependabot section below and require approval before pushing to PR branches.

## Go unavailable

Go is needed for native `onyx-cli`/`ods` builds and Go tests, but not for most repo development workflows when released wheels are used.

Symptoms:

- `go: command not found`
- `go test ./...` cannot run for `cli` or `tools/ods`
- `uv build --wheel` fails while trying to compile the Go binary

Recovery:

- Treat native Go tests as optional unless the task is changing CLI/ods Go source.
- Install Go 1.24+ before native builds/tests.
- If Go is unavailable during skill construction or review, record native CLI/ods test execution as a known gap rather than claiming it passed.

## GitHub CLI and remote side effects

Symptoms:

- `gh: command not found`
- `gh auth status` fails
- `ods run-ci`, `ods cherry-pick`, or `ods trace` cannot find runs/PRs

Recovery:

```bash
gh auth login
gh auth status
```

Remote operations require explicit approval:

- `ods run-ci` pushes branches and creates/updates PRs unless `--dry-run` is used.
- `ods cherry-pick` can create commits, push branches, create PRs, or dispatch workflows.
- `gh pr review`, `gh pr merge`, `gh pr close`, rerunning CI, release tagging, and pushing fixes alter shared state.

Use `--dry-run` first where available.

## AWS and S3-backed workflows

Symptoms:

- `aws: command not found`
- `ods screenshot-diff` cannot fetch/upload baselines
- `ods audit` cannot read/write the advisory allowlist
- `ods db restore --fetch-seeded` cannot download the seeded snapshot

Recovery:

```bash
aws sts get-caller-identity
aws sso login
# or use the user's approved non-SSO AWS credential setup
```

Do not create, upload, delete, or overwrite S3 artifacts without approval. `ods screenshot-diff upload-baselines --delete` and audit allowlist updates affect shared gates.

## Environment files and secrets

Common env files and sources:

| Area | Local file/source | Notes |
| --- | --- | --- |
| `onyx-cli` | user config plus `ONYX_*` env vars | Env overrides file config; PAT is sensitive. |
| Guided deployment | deployment `.env` | Created from a bundled template; `onyx-cli deploy upgrade` preserves edits. |
| Source backend dev | developer `.env` | `ods backend` creates it from the repo template if missing; shell env wins. |
| Tests | process env, local ignored env files, or secrets manager | If required secrets are absent, ask the user rather than silently skipping required tests. |

Rules:

- Never commit secrets or generated local `.env` files.
- For auth failures, check server URL, API prefix, PAT, and user permissions.
- For Compose startup failures, verify `USER_AUTH_SECRET`, Postgres password, image tag, and any SSO/SMTP/OAuth values that were intentionally configured.
- For Helm, avoid copying Docker Compose service hostnames into Kubernetes config; underscores are invalid in Kubernetes DNS labels.

## Postgres access fallback

Use read-only SQL probes first:

```bash
PGPASSWORD="${POSTGRES_PASSWORD:-password}" \
  psql -h "${POSTGRES_HOST:-localhost}" -U postgres -c "SELECT 1;"
```

If `psql` is unavailable on the host but the standard compose container is running:

```bash
docker exec onyx-relational_db-1 psql -U postgres -c "SELECT 1;"
```

Do not add `-it` in agent shells. Confirm the Compose project/container name before using the fallback on non-default stacks. Require approval for write SQL, schema changes, restore, drop, or volume removal.

## Generated Compose drift

Symptoms:

- Pre-commit rewrites compose files.
- CLI deploy embedded-file drift tests fail.
- Review shows generated default/prod/no-letsencrypt compose files edited directly.

Recovery:

```bash
ods generate-compose
ods generate-compose --write
```

Rules:

- Change the shared compose template for generated variants.
- Include regenerated outputs and refreshed embedded deployment copies together.
- Use the no-write form as a check in CI or review.

## Helm/Kubernetes blockers

Symptoms:

- `helm: command not found`
- `helm dependency update` fails
- `helm template` fails on Craft Kubernetes version guard
- Pods fail DNS lookups after copying Compose env values
- External secrets are not materialized at first install

Recovery:

```bash
helm dependency update deployment/helm/charts/onyx
helm template test-output deployment/helm/charts/onyx \
  --set auth.opensearch.values.opensearch_admin_password='StrongPassword123!'
```

Guidance:

- Install Helm and kubectl before chart work.
- Craft Helm deployments require Kubernetes 1.33+.
- External Secrets Operator must be installed separately before enabling external secrets.
- A short `CreateContainerConfigError` window can occur while ESO materializes a secret; persistent errors mean the secret store/path/keys/permissions are wrong.
- Confirm before `helm uninstall` or PVC deletion.

## Merge queue and Dependabot caveats

This is specialized, de-prioritized knowledge. Use it only when the user asks to land Dependabot or similar bot-authored PRs; otherwise route normal GitHub work through the task-specific instructions.

Onyx main is protected by merge queue:

- Enqueue with `gh pr merge <pr> --auto` after approval; do not pass `--squash`, `--merge`, or `--rebase`.
- Required checks include aggregate jobs for integration and Playwright matrices. If an aggregate job is absent, the matrix may still be running rather than blocked.
- Green CI proves build/test status, not semantic safety. Major bumps and 0.x minor bumps need compatibility review.
- Approving, closing, pushing to PR branches, rerunning CI, and enqueueing are remote side effects. Confirm the bucketed plan before acting.

Known mechanical cases:

- Python dependency bumps can leave exported backend requirement files stale. The same pre-commit hooks used by CI should regenerate them.
- JavaScript dependency bumps can leave Bun lockfiles stale. Run Bun install in the relevant package directory.
- If two PRs bump the same package, identify superseded duplicates before closing anything.
- If a Dependabot branch has not been manually modified and conflicts with main, ask Dependabot to rebase rather than pushing over it.

## Command output too large or interactive

- Use `onyx-cli ask --max-output 0` only when the downstream consumer can handle a full response.
- Use `onyx-cli search --max-output 0` only when large valid JSON is acceptable; otherwise read the `truncation.full_response_path` when needed.
- Use `ods logs --follow=false --tail <n>` and `onyx-cli deploy logs --tail <n>` for bounded logs.
- Prefer `--json`, `--dry-run`, `--no-open`, `--list`, and `--no-prompt` only when their side effects and defaults are understood.

## Unsafe or service-dependent evidence not bundled as scripts

No runnable helper scripts are bundled with this sub-skill because the useful operations are service-dependent and can alter Docker hosts, databases, remote GitHub state, Kubernetes clusters, S3 baselines, or deployments. The references provide concrete command forms and safety gates instead. Use command-specific dry-run/read-only modes first, then ask the user before side effects.
