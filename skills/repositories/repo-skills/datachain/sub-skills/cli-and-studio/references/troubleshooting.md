# CLI and Studio Troubleshooting

## Purpose

Use this reference to diagnose predictable DataChain CLI and Studio failures
without reopening source material. Start by identifying the command family:
storage, dataset/display, Studio auth/job/pipeline, skill installer, or config.

## Auth and Team Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Not logged in to Studio. Log in with 'datachain auth login'.` | A command explicitly selected Studio (`--studio`, `job`, `pipeline`, or Studio dataset mutation) but no token is configured. | Run `datachain auth login`, set masked `DATACHAIN_STUDIO_TOKEN`, or switch to local mode if Studio was not intended. |
| `Studio token is not set... DATACHAIN_STUDIO_TOKEN` | Studio client was constructed without token from env/config. | Provide `DATACHAIN_STUDIO_TOKEN` or login. Do not paste token into logs or final responses. |
| `Studio team is not set... DATACHAIN_STUDIO_TEAM` | Studio client needs a team and none came from `--team`, env, or config. | Run `datachain auth team TEAM`, pass `--team TEAM`, or set `DATACHAIN_STUDIO_TEAM`. |
| `Not authorized for the team ...` | Token is missing access to the selected team. | Confirm the team name, re-login with appropriate `--team` scoping, or ask the user for a token/team with access. |
| `Token already exists... logout using ...` during login | Config already has a token for the same Studio host. | Confirm with the user, then run `datachain auth logout` or `datachain auth logout --local` before logging in again. |

Safety: `datachain auth token` prints a secret. Use it only for explicit token
inspection and avoid copying the value into shared output.

## Local vs Studio Flavor Confusion

Symptoms:

- `datachain ls` or `datachain dataset ls` does not show Studio entries.
- `datachain ... --all` only shows local entries.
- `--studio` fails while default command succeeds.

Rules and recovery:

1. No flavor flag defaults to local.
2. `--all` needs a token to include Studio; without a token it falls back to
   local.
3. `--studio` requires Studio auth and team context.
4. Use `--local --studio` or `--all` when both local and Studio rows are needed.
5. For dataset names, use fully qualified `namespace.project.name` or
   `@namespace.project.name` in Studio-heavy workflows to avoid environment
   default surprises.

## Public vs Private Storage

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Access denied, forbidden, or credential errors on `ls`, `du`, `find`, `cp`, `clone`, or `index` | Private bucket without provider credentials, or incorrect provider profile. | Remove `--anon`, configure the provider credential chain, and run `bucket status` first. |
| Public bucket fails with credential lookup noise | CLI is attempting authenticated access to a public bucket. | Add `--anon` for public S3/GCS/Azure-compatible paths. |
| Azure public/anonymous check is inconclusive | Azure anonymous detection needs a storage account name. | Run `datachain bucket status --account-name ACCOUNT az://container/`. |
| Copy/clone expands unexpected paths | Shell or DataChain glob expansion matched more objects than expected. | Quote the URI and use `--no-glob` if the pattern should be literal. |
| Large copy starts unexpectedly | `cp`/`clone` is mutating and may download many files. | Run `ls`, `du`, or `find` first; require `-r` for directory copies and confirm output path. |

## Dataset and `show` Confusion

- `datachain show NAME` inspects a saved dataset, not raw object storage. Use
  `datachain ls URI` for storage paths.
- If `show` output lacks fields, try `--schema` to append the schema and
  `--hidden` to include hidden fields.
- `--columns` expects comma-separated dataset column names; invalid or unknown
  columns fail when the dataset query is executed.
- `--script` prints the saved query script and returns without row display.
- `--no-collapse` changes display shape for nested/flattened columns; use it when
  collapsed nested fields hide details the user expects.
- `dataset ls NAME` shows versions for that named dataset; plain `dataset ls`
  groups each dataset to its latest version unless `--versions` is supplied.

## Mutating Dataset Commands

Before `dataset rm/remove`, confirm:

- local versus Studio (`--studio` changes the remote target);
- full dataset name and namespace/project;
- version (`--version` or `name@version`);
- whether `--force` is intended.

Before `dataset edit`, confirm the target and whether a fully qualified
non-local name will route to Studio. Missing Studio auth during remote edit/remove
is expected; login or switch to a local dataset target.

Before `dataset pull`, confirm whether `--cp` should copy files in addition to
registering local dataset state.

## Job Logs, Cancellation, and Reconnects

Symptoms and facts:

- Ctrl+C or closing `datachain job logs JOB_ID` only stops local log display.
  The Studio job keeps running.
- `job run` without `--no-wait` follows logs/status. `--no-wait` returns after
  creation; `--no-follow` waits for status but suppresses live log text.
- If websocket logs disconnect while the job is still active, the CLI reports a
  reconnect failure and suggests `datachain job logs JOB_ID`. The job may still
  be running.
- Failed log blob fetches can print `Warning: Failed to fetch logs from studio`
  while the job itself may still finish.

Recovery:

1. Use `datachain job ls --status RUNNING --team TEAM` or Studio UI to confirm
   status.
2. Use `datachain job logs JOB_ID --team TEAM` to resume monitoring.
3. Use `datachain job cancel JOB_ID --team TEAM` to stop a job. Confirm the job
   ID and team first.
4. For repeated dependency/install failures, reduce requirements, pin versions,
   or test the script locally before re-running remotely.

## Scheduled Job vs Immediate Run

- `job run --start-time ...` schedules a one-time future task; it does not start
  immediately.
- `job run --cron ...` schedules recurring execution. With no `--start-time`, the
  schedule starts from the current time.
- Scheduled tasks do not stream logs at submission time. Use Studio UI or job
  listing/log commands after a concrete run exists.
- Natural-language `--start-time` values depend on date parsing. If parsing
  fails, use an ISO-like timestamp.

## Pipeline Pitfalls

- `pipeline create` creates the pipeline in paused state for review. It does not
  immediately start dataset updates until resumed.
- `pipeline pause` lets currently running jobs continue; it blocks new jobs from
  starting.
- `pipeline remove-job` only works on paused pipelines and pending jobs. Use
  `pipeline status` to identify pending job IDs.
- `pipeline list --status failed --search DATASET` is a good first step before a
  deeper `pipeline status NAME` inspection.

## Skill Installer Confusion

- `datachain skill list` is read-only and shows available DataChain bundled
  skills and supported target names.
- `datachain skill install` and `datachain skill uninstall` mutate target agent
  directories. Omitting the skill list applies to all bundled skills.
- `--local` resolves paths from the current working directory. `cd` to the
  intended project root before local install/uninstall.
- Use [skill_layout_check.py](../scripts/skill_layout_check.py) to preview target
  paths. Route detailed target layout behavior to sibling
  [`agent-harness`](../../agent-harness/SKILL.md).

## Parser Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Use 'datachain COMMAND --help' to see available options` | A command family was supplied without a required subcommand, such as `bucket`, `dataset`, `auth`, `job`, `pipeline`, or `skill`. | Run the nested `--help` command and choose a subcommand. |
| `invalid choice` | Command/subcommand or target name is misspelled. | Check [CLI reference](cli-reference.md) for exact command names; remember `dataset` has alias `ds` and `dataset rm` has alias `remove`. |
| Verbosity flag rejected at top level | `-v` and `-q` are command-scoped in usage output. | Put them after the command/subcommand, for example `datachain ls -v URI` or `datachain job run -v query.py`. |
| Invalid `find` column | `-c/--columns` contains a value outside `path,name,size,type,du`. | Use a comma-separated subset of valid columns. |
| Missing argument after `--env`, `--req`, or `--columns` | Option requires one or more values. | Quote shell-sensitive values and keep `KEY=VALUE` pairs intact. |

## Maintenance Command Safety

- `gc` deletes temporary tables, failed dataset versions, and outdated
  checkpoints. It is not a dry-run status command.
- `clear-cache` clears local file cache.
- `index` mutates local catalog/index state.
- `cp` and `clone` create output files; `clone` also registers local dataset
  state. Use `du`/`find` first for size checks.
