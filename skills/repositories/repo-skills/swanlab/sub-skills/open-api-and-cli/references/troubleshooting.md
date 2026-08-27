# Open API and CLI Troubleshooting

## Invalid path shape

Symptoms:

- `ValueError: project path must contain 2 non-empty segment(s)`
- `ValueError: run path must contain 3 non-empty segment(s)`
- CLI command exits before the API call because a required path argument is
  missing.

Fix:

- Workspace/user path: `workspace`
- Project path: `workspace/project`
- Run path: `workspace/project/run`
- Remove leading/trailing spaces and doubled slashes.
- Do not pass a run path to project-list/filter methods, and do not pass a
  project path to run-info/metric methods.

## Invalid project name or visibility

Project creation validates locally before the request:

- Name length must be 1-100 characters.
- Allowed characters are `0-9`, `a-z`, `A-Z`, `-`, `_`, `.`, `+`.
- Spaces, slashes, at-signs, and non-ASCII project names are rejected.
- Visibility must be `PUBLIC` or `PRIVATE` in Python, or `public|private` in
  the CLI.

Fix invalid names before retrying; do not expect the backend to normalize them.

## Missing or blank API key

Symptoms:

- Authentication error mentioning no API key.
- CLI query command fails before printing a normal `ok` response.

Fix:

- For Python, pass `api_key` explicitly or ensure SwanLab settings/login state is
  already configured:

  ```python
  import os, swanlab
  api = swanlab.Api(api_key=os.environ["SWANLAB_API_KEY"])
  ```

- For CLI automation, pass `--api-key` and optionally `--host`, or run in an
  environment where SwanLab settings are already configured.
- Do not use this sub-skill for storing credentials; credential storage and
  `swanlab login` are owned by settings-and-modes.
- Blank strings are treated as missing keys.

## Host errors

A blank host raises a validation error. Pass a real API host or omit `host` so
settings can supply one. When using a self-hosted deployment, keep the API host
and web host pairing consistent through the supported settings/login flow.

## 4xx/5xx HTTP behavior

The entity base class wraps HTTP exceptions and stores an error instead of
crashing the process. Consequences vary by helper:

- Entity properties usually fall back to `""`, `False`, `{}`, or `[]`.
- `.wrapper().json()` collects stored errors into `errmsg` and sets `ok` false.
- Project/run deletion returns `False` on failed requests.
- Project creation returns `None` on failed create requests.
- Self-hosted mutators return `ok=False` when the request itself fails after
  local permission checks pass.

Debugging pattern:

```python
resp = api.project("alice/demo").wrapper().json()
if not resp["ok"]:
    print(resp["errmsg"])
```

If a property is empty, rerun the same entity through `.wrapper().json()` before
assuming the remote object truly lacks that field.

## Pagination and `all=True` surprises

Symptoms:

- Only one page is returned.
- A page-size error appears before the request.
- Full export is unexpectedly large.

Fix:

- Use `all=True` in Python or `--all` in CLI to auto-fetch all pages.
- Use allowed page sizes: `10, 12, 15, 20, 24, 27, 50, 100`.
- Remember that `all=True` is client-side; it repeatedly requests pages until
  the backend reports the last page.
- For scalar metrics, `all=True` switches to a full-resolution export path. Use
  sampled queries or range flags for large runs.

## Filter JSON errors

Symptoms:

- `filter_query must not be empty`
- `neither a valid file path nor valid JSON`
- `filter_query must resolve to a JSON array`
- `Missing required fields`
- `Invalid STABLE key`, `Invalid type`, or `Invalid filter op`

Fix:

```bash
swanlab api run filter alice/demo \
  --filter_query '[{"key":"state","type":"STABLE","op":"EQ","value":["RUNNING"]}]'
```

Checklist:

- The top-level JSON value must be an array.
- Each filter item needs `key`, `type`, `op`, and `value`.
- `value` must be an array, even for one item.
- Shell quoting must preserve valid JSON double quotes.
- If a path is supplied instead of inline JSON, the file must exist and contain
  a JSON array.

## Group and sort validation errors

Groups require `key` and `type`. Sorts require `key`, `type`, and `order`.
Allowed sort orders are `ASC` and `DESC`. Stable-key validation applies when
`type` is `STABLE`.

Use `Project.runs(filters=..., groups=..., sorts=...)` for group/sort control.
The top-level `Api.runs()` convenience method accepts filters only.

## Metric key and range errors

Symptoms:

- `keys must be a non-empty list of non-empty strings`
- `Invalid metric_type`
- `key is required for metric_type 'SCALAR'`
- `head and tail are mutually exclusive`
- `last is mutually exclusive with start/end`

Fix:

- Pass metric keys as a Python list or CLI comma-separated string with no blank
  entries.
- Use `SCALAR` or `MEDIA` for metric key listings and data queries.
- Use `logs()` / `swanlab api run logs` for log data, not `Metrics(...,
  metric_type="LOG")`.
- Use `series()` to discover exact keys before querying data.
- For range queries, pick only one of `head`/`tail`, and do not combine `last`
  with `start` or `end`.

## Deprecated columns versus series

Column APIs and CLI `run column(s)` commands are deprecated. They may still work
for compatibility, but current metric key discovery should use `series()` or
`swanlab api run series`. Use `metrics()` for scalar values and `medias()` for
media values.

## Media and export URL issues

Media metric responses and scalar/log export helpers often return presigned URLs.
If the response is `ok=False`, inspect `errmsg`. If the response is `ok=True` but
contains no URL, the backend may have returned an unexpected payload or the
presigned URL lookup failed.

CSV export is scalar-only. Media keys return an `ok=False` CSV export response.
The CLI saves JSON; use Python key objects when the task specifically requires a
scalar CSV export URL.

## Self-hosted root or expired checks

Root-only self-hosted helpers validate local instance status before the admin
request:

- Expired instance: raises an error mentioning expiration.
- Non-root user: raises an error asking for root permission.
- Blank `create_user` username/password: raises before the request.

First inspect status:

```python
sh = api.self_hosted()
print(sh.enabled, sh.expired, sh.root, sh.plan, sh.seats)
```

Then call root-only commands only if the authenticated API key belongs to a root
user on a non-expired self-hosted instance.

## Non-interactive CLI use

Safe:

```bash
swanlab api --help
swanlab api run metrics --help
```

For real queries in scripts:

```bash
swanlab api run summary alice/demo/run-abc \
  --keys train/loss,eval/acc \
  --api-key "$SWANLAB_API_KEY" \
  --save summary.json
```

Guidelines:

- Supply all required positional arguments and flags.
- Use `--save FILE` or parse stdout JSON.
- Do not rely on interactive login prompts in batch jobs.
- Run help commands when constructing a command dynamically; help exits before
  `Api` is constructed.

## No-network validation

Run the bundled validation script when changing this skill or when you need to
confirm local validation behavior without contacting SwanLab services:

```bash
python skills/disco/swanlab/sub-skills/open-api-and-cli/scripts/check_api_validation.py
```

The script uses validation helpers, Click help, and mocked clients only. It does
not require an API key.
