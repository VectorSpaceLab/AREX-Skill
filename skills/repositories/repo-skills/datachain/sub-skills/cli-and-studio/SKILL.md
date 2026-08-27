---
name: cli-and-studio
description: "Guides DataChain CLI commands, dataset and storage command
  routing, Studio auth/jobs/pipelines, and environment configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Studio

Use this sub-skill when the user asks how to choose or run `datachain` CLI
commands, diagnose command parser behavior, route storage versus dataset
operations, authenticate with DataChain Studio, run or monitor Studio jobs,
manage Studio pipelines, configure CLI/Studio environment variables, or inspect
DataChain bundled skill install targets.

## Trigger Phrases

Load this sub-skill for prompts containing or implying:

- `datachain --help`, `datachain -V`, verbose/quiet behavior, parser errors, or
  command-specific `--help` output;
- storage commands: `bucket status`, `cp`, `clone`, `ls`, `du`, `find`, `index`,
  public/private buckets, `--anon`, `--studio`, `--local`, or `--all`;
- dataset/display commands: `dataset`, `ds`, `dataset ls`, `dataset rm`,
  `dataset remove`, `dataset edit`, `dataset pull`, or `show`;
- maintenance commands: `gc`, `clear-cache`, outdated checkpoints, temporary
  tables, or local cache cleanup;
- Studio commands: `auth login`, `auth token`, `auth team`, `auth logout`,
  `job run`, `job logs`, `job cancel`, `job clusters`, `pipeline create`,
  `pipeline list`, `pipeline pause`, `pipeline resume`, `pipeline status`, or
  `pipeline remove-job`;
- `datachain skill install`, `datachain skill list`, `--target`, `--local`,
  Claude/Cursor/Codex/Pi/Copilot target selection, and safe layout previews;
- `DATACHAIN_ROOT_DIR`, `DATACHAIN_GLOBAL_CONFIG_DIR`,
  `DATACHAIN_SYSTEM_CONFIG_DIR`, `DATACHAIN_NO_ANALYTICS`,
  `DATACHAIN_STUDIO_URL`, `DATACHAIN_STUDIO_TOKEN`, `DATACHAIN_STUDIO_TEAM`,
  `DATACHAIN_NAMESPACE`, `DATACHAIN_PROJECT`, or
  `DATACHAIN_IGNORE_CHECKPOINTS`.

## First Decision

1. **Need a command catalog or parser default** → read
   [CLI reference](references/cli-reference.md). If the user only needs to
   verify help output safely, run
   [cli_help_smoke.py](scripts/cli_help_smoke.py) with a command path such as
   `job run` or `dataset ls`; the helper appends `--help` and avoids credentialed
   operations.
2. **Need Studio auth, jobs, scheduling, logs, clusters, or pipelines** → read
   [Studio and jobs](references/studio-and-jobs.md). Confirm token/team and
   scheduling intent before running any Studio mutation.
3. **Need environment variables, config precedence, namespace/project defaults,
   or token handling** → read [configuration](references/configuration.md).
4. **Need error diagnosis** → read
   [troubleshooting](references/troubleshooting.md), especially for missing
   auth, local-vs-Studio flavor confusion, storage access, `show`/schema
   confusion, job-log cancellation misconceptions, scheduled jobs, and parser
   errors.
5. **Need DataChain bundled skill target layouts** → use
   [skill_layout_check.py](scripts/skill_layout_check.py) for a dry-run layout
   preview, then route detailed target-layout and installed-skill behavior to
   sibling [`agent-harness`](../agent-harness/SKILL.md).

## Command Routing Rules

- Use **storage commands** when the subject is a URI/path or object-storage
  listing/copy/index task (`s3://`, `gs://`, `az://`, `hf://`, `file://`, local
  paths). Storage `ls` is not the same as `dataset ls`.
- Use **dataset commands** when the subject is a named saved DataChain dataset
  and version (`name`, `namespace.project.name`, or `name@version`). Use `show`
  to inspect dataset rows, schema, or query script.
- Use **Studio flavor flags** deliberately. For `ls` and `dataset ls`, no flavor
  flag defaults to local. `--studio` requires Studio auth; `--all` lists both
  only when a token is available and otherwise falls back to local.
- Use **Studio job commands** for remote execution of a query file. `job run`
  submits work to Studio and may keep running after local log output stops.
- Use **pipeline commands** for Studio-managed dependency pipelines over dataset
  updates. Pipelines are separate from Python SDK pipeline authoring.
- Use **skill commands** only for DataChain's bundled agent-skill installer; the
  knowledge-base methodology and installed agent skill content are owned by
  `agent-harness`.

## Safety Rules

- Prefer `datachain <command> --help` or the bundled help smoke helper before
  composing unfamiliar commands.
- Treat these as mutating: `cp`, `clone`, `index`, `dataset pull`, `dataset edit`,
  `dataset rm/remove`, `gc`, `clear-cache`, `auth login/logout/team`, `job run`,
  `job cancel`, `pipeline create/pause/resume/remove-job`, and
  `skill install/uninstall`.
- Before a mutating command, confirm the dataset name/version, output directory,
  Studio team, target agent, and whether the operation is local or Studio-scoped.
- Do not print, paste, commit, or store real Studio tokens, cloud credentials, or
  secret `--env` values. `datachain auth token` intentionally prints a secret;
  use it only when the user explicitly asks to inspect or copy the token.
- For public buckets, `--anon` is acceptable. For private storage, verify the
  credential source and consider `bucket status` before listing or copying.
- Closing `job run` or `job logs` output does not cancel a Studio job. Use
  `datachain job cancel <id>` for cancellation.
- Do not route Python SDK chain construction, UDF signatures, `.save()`, or
  `read_storage` code patterns here; send those to `../sdk-pipelines/`.
- Do not route query expression operators/functions here; send those to
  `../query-engine/`.
- Do not route repo contributor testing, backend matrix development, or release
  work here; send those to `../repo-development/`.

## Native Verification Candidates Owned Here

- Parser and flavor defaults: CLI parsing, `-v/-q`, `bucket status`, and
  `determine_flavors` unit coverage.
- Skill command behavior: bundled skill list/install target parsing and layout
  rules; use the layout helper instead of performing real installs during
  usability checks.
- CLI end-to-end candidates: storage `ls/du/find/cp/clone`, dataset `ls/edit/rm`,
  and `gc`; mark network/object-copying steps as side-effecting unless run in a
  controlled fixture.
- Studio candidates: auth login/logout/token/team, dataset Studio edit/remove,
  job run/log/cancel/clusters, reconnect behavior, checkpoint reuse, and
  scheduled-job behavior with mocked Studio responses.
