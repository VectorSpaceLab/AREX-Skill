# SwanLab `api` CLI Reference

Use `swanlab api` or `python -m swanlab api` for command-line access to the
same public query/admin concepts described in `swanlab.Api`.

Help commands are safe to run without credentials:

```bash
swanlab api --help
swanlab api run metrics --help
python -m swanlab api self-hosted --help
```

Query/admin commands require valid credentials and network access.

## Common leaf-command options

Every leaf command is wrapped with the same host/auth options:

| Option | Meaning |
| --- | --- |
| `-h, --host TEXT` | API host to use for this invocation. |
| `-k, --api-key, --api_key TEXT` | API key for this invocation. |
| `--save [TEXT]` | Save the JSON payload. With a filename, writes that file. Without a filename, creates a timestamped `swanlab-...json` file in the current directory. |
| `--help` | Print help and exit before constructing `Api`; safe and non-networked. |

If `--host` and `--api-key` are omitted, the command uses the configured SwanLab
settings/login state. Storage and login setup are outside this sub-skill.

All normal command output is pretty JSON with this envelope:

```json
{
  "ok": true,
  "errmsg": "",
  "data": {}
}
```

Errors reported through the API wrapper use `ok: false` and a non-empty
`errmsg`. Argument and JSON parsing errors are reported by Click before the API
call.

## Command map

### Project commands

| Command | Purpose | Key flags/args |
| --- | --- | --- |
| `swanlab api project info PATH` | Get one project. | `PATH` is `workspace/project`; `--save`; common auth flags. |
| `swanlab api project list` | List projects in a workspace. | `--workspace`; `-n/--page_num`; `-s/--page_size`; `--all`; `--save`. |
| `swanlab api project create` | Create a project. | `-n/--name` required; `-v/--visibility public|private`; `-d/--description`; `-w/--workspace`; `--save`. |

`--page_size` for project listing is constrained to `10, 12, 15, 20, 24, 27,
50, 100`. Project names must be 1-100 characters using only `0-9a-zA-Z-_.+`.

### Workspace and user commands

| Command | Purpose |
| --- | --- |
| `swanlab api workspace info USERNAME` | Get workspace metadata for one username. |
| `swanlab api user info` | Get current authenticated user metadata. |

Both support `--save` and common auth flags.

### Run/experiment commands

| Command | Purpose | Key flags/args |
| --- | --- | --- |
| `swanlab api run info PATH` | Get one run. | `PATH` is `workspace/project/run`; `--save`. |
| `swanlab api run list PROJECT_PATH` | List runs with GET pagination. | `PROJECT_PATH`; `-n/--page_num`; `-s/--page_size`; `--all`; `--save`. |
| `swanlab api run filter PROJECT_PATH` | Filter runs with POST filter rules. | `-f/--filter_query` required; `--save`. |
| `swanlab api run series PATH` | List scalar/media metric keys. | `--type scalar|media`; `--class custom|system`; `--search`; `--save`. |
| `swanlab api run metrics PATH` | Get scalar metric data. | `--keys`; `--sample`; `--ignore-timestamp`; `--all`; range flags; `--save`. |
| `swanlab api run summary PATH` | Get scalar summaries. | Optional `--keys`; `--save`. |
| `swanlab api run medias PATH` | Get media metrics. | `--keys`; `-s/--step`; `--all`; `--save`. |
| `swanlab api run logs PATH` | Get console logs. | `-o/--offset`; `-l/--level debug|info|warn|error`; `--ignore-timestamp`; `--save`. |
| `swanlab api run export-logs PATH` | Export logs as a downloadable log URL. | `--start`; `-r/--rows` from 1 to 500000; `--save`. |
| `swanlab api run columns PATH` | Deprecated column listing. | Paging, `--search`, `--class`, `--type`, `--all`, `--save`. |
| `swanlab api run column PATH` | Deprecated single-column lookup. | `--key`; `--class`; `--type`; `--save`. |

Run list page sizes are constrained to `10, 12, 15, 20, 24, 27, 50, 100`.
Column commands are compatibility-only; prefer `series`, `metrics`, and
`medias` for new workflows.

### Self-hosted commands

| Command | Purpose | Key flags/args |
| --- | --- | --- |
| `swanlab api self-hosted info` | Show self-hosted instance status. | `--save`; common auth flags. |
| `swanlab api self-hosted create-user` | Create a user. | `-u/--username`; `-p/--password`; root-only; `--save`. |
| `swanlab api self-hosted list-users` | List users. | `-n/--page_num`; `-s/--page_size`; `--all`; root-only; `--save`. |
| `swanlab api self-hosted list-projects` | List all projects. | Paging, `--all`, `--search`, `--creator`, `--workspace`; root-only; `--save`. |
| `swanlab api self-hosted list-workspaces` | List all workspaces. | Paging, `--all`, `--search`; root-only; `--save`. |
| `swanlab api self-hosted summary` | Show system usage summary. | Root-only; `--save`. |

Self-hosted admin commands validate expiration and root permission before the
remote admin call. Prefer page sizes from the standard allowed set even where
Click accepts any integer, because backend pagination validation is stricter.

## Filter JSON for `run filter`

`--filter_query` accepts either an inline JSON array string or a path to a JSON
file. The resolved JSON must be an array of filter dictionaries:

```bash
swanlab api run filter alice/demo \
  --filter_query '[{"key":"state","type":"STABLE","op":"EQ","value":["RUNNING"]}]'
```

Valid filter fields:

- `key`: metric/config key or a stable key such as `state`, `name`, `cluster`,
  `createdAt`, or `labels`.
- `type`: `STABLE`, `CONFIG`, or `SCALAR`.
- `op`: `EQ`, `NEQ`, `GTE`, `LTE`, `IN`, `NOT IN`, or `CONTAIN`.
- `value`: JSON array, even for a single value.

Common failures:

- Empty `--filter_query`.
- Invalid JSON quoting in the shell.
- JSON object instead of JSON array.
- A string that is neither an existing file nor valid JSON.
- A filter item missing `key`, `type`, `op`, or `value`.

## Scalar metric range flags

`run metrics` supports sampled, full, and range queries:

```bash
swanlab api run metrics alice/demo/run-abc \
  --keys train/loss,eval/acc \
  --sample 1500

swanlab api run metrics alice/demo/run-abc \
  --keys train/loss \
  --range-type step --range-start 0 --range-end 500

swanlab api run metrics alice/demo/run-abc \
  --keys train/loss \
  --range-last 300000 --range-tail 50
```

Range constraints are enforced before the API call:

- `--range-head` and `--range-tail` cannot be used together.
- `--range-last` cannot be combined with `--range-start` or `--range-end`.
- `--range-start` must be less than or equal to `--range-end`.

`--all` requests full scalar data through the export path and full media data
through the all-media endpoint. Large full-resolution results can be slow and
large; use ranges or sampled queries when possible.

## JSON, CSV, and export output

The CLI prints and saves JSON. It does not write raw CSV files directly.
Scalar CSV export URLs are available from the Python API key objects. CLI
log export returns JSON containing a downloadable log URL when the backend
succeeds:

```bash
swanlab api run export-logs alice/demo/run-abc --start 0 --rows 500000 --save logs-url.json
```

For shell automation, capture JSON to a file with `--save output.json` or pipe
stdout to a JSON parser. Avoid commands that require interactive login in
non-interactive jobs; pass credentials through the common auth flags or ensure
settings are already configured.

## Safe non-interactive checks

These commands should not prompt or contact the network:

```bash
swanlab api --help
swanlab api project --help
swanlab api run metrics --help
swanlab api self-hosted list-projects --help
```

The bundled `../scripts/check_api_validation.py` script also verifies CLI help,
filter parsing, path/name validation, pagination flags, and error behavior with
mocked clients only.
