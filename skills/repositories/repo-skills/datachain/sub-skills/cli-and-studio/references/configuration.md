# CLI and Studio Configuration

## Purpose

Read this reference when a DataChain CLI or Studio command depends on root
directories, config precedence, default namespace/project, Studio URL/token/team,
analytics, or checkpoint behavior. Keep credentials out of commands and files
unless the user explicitly approves where they will be stored.

## Config Levels and Precedence

DataChain reads configuration from system, global, and local levels. Normal reads
merge them in that order, so local project config can override global config,
and global config can override system config. Commands that explicitly write
with `--local` update local config; otherwise auth commands usually write global
config.

Important consequences:

- Use project-local config only for project-specific Studio hosts, teams, or
  temporary auth state.
- Do not commit local DataChain config if it contains tokens or team-specific
  secrets.
- Environment variables can override config for specific behaviors and are often
  safer for CI when secrets are masked.

## Core Directory and Config Environment Variables

| Variable | Effect | Safe usage |
| --- | --- | --- |
| `DATACHAIN_ROOT_DIR` | Sets the parent directory where the default `.datachain/` root is created. Without it, the default parent is the current working directory. | Use in tests, CI, and temporary command runs to isolate DataChain state from a real project. |
| `DATACHAIN_DIR` | Lower-level override for the exact DataChain root directory instead of `<root>/.datachain`. | Use only when the exact internal root must be controlled. |
| `DATACHAIN_SYSTEM_CONFIG_DIR` | Overrides the platform-specific system config directory. | Mainly for controlled deployments or tests. |
| `DATACHAIN_GLOBAL_CONFIG_DIR` | Overrides the platform-specific user/global config directory. | Useful to isolate auth/config during automation. |
| `DATACHAIN_NO_ANALYTICS` | Disables telemetry when set. | Set in CI, tests, and privacy-sensitive sessions. |

When running safe inspection commands from automation, set `DATACHAIN_ROOT_DIR`
and config-dir overrides to temporary directories and set
`DATACHAIN_NO_ANALYTICS=1`. Remove the temporary directories afterward.

## Studio Environment Variables

| Variable | Effect | Notes |
| --- | --- | --- |
| `DATACHAIN_STUDIO_URL` | Overrides the Studio base URL. A trailing slash is stripped before `/api` is appended. | Use for self-hosted or staging Studio. |
| `DATACHAIN_STUDIO_TOKEN` | Supplies the Studio auth token and takes precedence over config for Studio API calls. | Treat as a secret; use masked CI variables. |
| `DATACHAIN_STUDIO_TEAM` | Supplies the Studio team and takes precedence over config for Studio API calls. | Prefer explicit `--team` when switching teams in one session. |

`datachain auth login` writes token config after an interactive/code auth flow.
`datachain auth team` writes the default team. Environment variables are often
better for non-interactive jobs because they do not persist secrets to disk.

## Namespace and Project Defaults

| Variable | Effect |
| --- | --- |
| `DATACHAIN_NAMESPACE` | Default namespace for dataset names that do not specify one. |
| `DATACHAIN_PROJECT` | Default project. If it contains one dot, DataChain interprets it as `namespace.project` and uses both parts. |

Dataset names supplied on the CLI can also be fully qualified. Use fully
qualified names when a command might run in an environment with different
defaults.

Examples with placeholder values:

```bash
export DATACHAIN_NAMESPACE="team-namespace"
export DATACHAIN_PROJECT="analytics"
# Or combine both:
export DATACHAIN_PROJECT="team-namespace.analytics"
```

## Checkpoint Controls

| Variable or flag | Effect |
| --- | --- |
| `DATACHAIN_IGNORE_CHECKPOINTS=1` or `true` | Ignores existing checkpoints and forces scripts to recreate datasets. |
| `datachain job run --ignore-checkpoints` | Sends a reset request for the Studio job and avoids resuming from a previous run's checkpoint lineage. |
| `datachain gc --checkpoint-ttl SECONDS` | Removes local checkpoints older than the TTL during garbage collection. |

Use checkpoint resets when stale checkpoint reuse would hide changed inputs or
code. Do not reset checkpoints for expensive jobs unless the user accepts the
extra compute cost.

## Credentials Guidance

- Prefer `datachain auth login` for interactive Studio use; prefer
  `DATACHAIN_STUDIO_TOKEN` for masked CI or ephemeral automation.
- `datachain auth token` prints a secret. If a token must be inspected, do not
  include it in the final answer, logs, or skill artifacts.
- Use `--local` auth/team writes only for project-specific settings. Global auth
  affects all projects for the current user.
- For cloud storage, DataChain relies on the relevant filesystem/provider
  credential chain. `--anon` is only for public buckets; do not use it for
  private buckets expecting credentials.
- For Studio jobs, avoid inline real secrets in command examples. If the user
  chooses `--env` or `--env-file`, keep values masked in any shared output.

## Safe Automation Pattern

For read-only CLI help/list inspection from a script, isolate DataChain state:

```bash
TMPDIR="$(mktemp -d)"
DATACHAIN_ROOT_DIR="$TMPDIR/root" \
DATACHAIN_GLOBAL_CONFIG_DIR="$TMPDIR/global-config" \
DATACHAIN_SYSTEM_CONFIG_DIR="$TMPDIR/system-config" \
DATACHAIN_NO_ANALYTICS=1 \
  datachain <command> --help
rm -rf "$TMPDIR"
```

The bundled [CLI help smoke helper](../scripts/cli_help_smoke.py) applies this
pattern for subprocess-based help checks and can also import the installed
parser directly.

## Internal or Developer-Facing Variables

DataChain also has internal variables for catalog backends, distributed UDF
workers, job IDs, query chunks, and tests. Do not set those for ordinary CLI or
Studio usage unless a maintainer workflow explicitly calls for them. Route
contributor backend/testing questions to `../repo-development/`.
