# CVAT CLI troubleshooting

Start by reproducing the failure with the smallest non-destructive command:

```bash
cvat-cli --version
cvat-cli <same-global-options> task ls
cvat-cli <same-global-options> task ls --json
```

Use `--debug` only for private diagnostics and redact logs before sharing.

## Authentication and server selection

| Symptom | Likely cause | Fix |
|---|---|---|
| CLI prompts for a password unexpectedly. | No selected profile, no `CVAT_ACCESS_TOKEN`, no `PASS`, and no password in `--auth`. | Use `--profile NAME`, set `CVAT_ACCESS_TOKEN` securely, or set `PASS` out of band with `--auth USER`. |
| `--profile is mutually exclusive with --server-host/--server-port/--auth`. | A saved profile was combined with explicit server or password auth. | Use either `--profile NAME` alone, or explicit `--server-host` with `CVAT_ACCESS_TOKEN`/`--auth`; do not mix. |
| Command goes to `http://localhost` instead of the intended server. | No profile, no `--server-host`, and no configured default server. | Run `cvat-cli config default-server https://server.example.org` or pass `--server-host`/`--profile`. |
| PAT appears ignored. | A profile was selected, or an explicit credential/server changed resolution behavior. | Check `cvat-cli profile default`, unset default profile if needed, or use an explicit non-profile server with `CVAT_ACCESS_TOKEN`. |
| 401/403 authentication failures. | Wrong/expired token, wrong password, missing organization permissions, token read-only, or server-side permission policy. | Recreate/revoke PAT as needed, confirm token permissions, include `--org SLUG` for organization resources, and test `task ls`. |
| TLS certificate verification fails. | Self-signed or untrusted certificate. | Prefer installing the CA certificate. Use `--insecure` only for trusted test/self-hosted servers. |

Credential safety checks:

- Search scripts and shell history for `--auth .*:`, raw PAT-looking values, and exported secrets before committing or sharing.
- Prefer `profile create` prompt mode or token file import over command-line token literals.
- Delete a local profile only removes local storage; revoke the token in CVAT if it might be compromised.

## Profile/config store errors

The profile store enforces strict permissions on POSIX systems. Errors mention expected modes such as `0700` for the parent directory and `0600` for the auth JSON file.

Fix pattern:

```bash
# Determine the store path without printing tokens, then repair permissions.
store=$(python - <<'PY'
from cvat_sdk.core.auth import get_auth_store_path
print(get_auth_store_path())
PY
)
chmod 700 "$(dirname "$store")"
[ ! -e "$store" ] || chmod 600 "$store"
```

Other profile signals:

- `Unknown profile 'NAME'. Run 'cvat-cli profile list'.` means select an existing profile or create it.
- `Cannot combine a server value with --unset.` applies to `config default-server SERVER --unset`; use either a value or `--unset`.
- `A server URL with a port and '--server-port' cannot be used together.` means remove one of the port specifications.
- `Profile 'NAME' already exists. Pass '--force' to overwrite.` means use a new name, delete the old profile, or intentionally pass `--force`.

## Command grammar errors

| Symptom | Fix |
|---|---|
| `invalid choice` near a resource/action. | Use `task`, `project`, `profile`, `config`, or `function`, then a valid action. Do not rely on deprecated task aliases in new scripts. |
| `task create` reports missing `resource_type` or `resources`. | Put `local`, `share`, or `remote` after task options, followed by at least one path or URL. |
| JSON label parse failure. | `--labels` accepts either a file path or a JSON string. Validate files with `python -m json.tool labels.json`. Quote inline JSON with single quotes in POSIX shells. |
| `--function-module` and `--function-file` conflict or one is missing. | Exactly one is required for `task auto-annotate`, `function create-native`, and `function run-agent`. |
| `parameter type not specified` or unsupported parameter type. | Use `-p NAME=TYPE:VALUE` with type `int`, `float`, `str`, or `bool`. |
| `--conf-threshold` rejected. | It must parse as a float in `[0, 1]`. |

When in doubt, run the specific help command:

```bash
cvat-cli task create --help
cvat-cli task auto-annotate --help
cvat-cli function create-native --help
```

## Dataset import/export problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Export/import waits too long or appears stuck. | Server-side background archive/import job is still processing. | Increase `--completion_verification_period` to reduce polling noise; check server health separately. |
| `task import-dataset` rejects labels. | Dataset label names/attributes do not match the existing task. | Inspect/align labels before import; route format-specific work to `../../dataset-ops/SKILL.md`. |
| `project import-dataset` creates no useful tasks. | The uploaded dataset lacks images or has incompatible labels. | Confirm the dataset includes image data and project labels match the dataset. |
| Export file unexpectedly huge. | `--with-images yes` included media. | Use `--with-images no` or omit the flag when only annotations are needed. |
| Filename omitted and output is hard to find. | Export/backup wrote to current directory with server-generated filename. | Pass an explicit output zip path or an output directory ending in a directory separator. |

## Frames command problems

- `task frames` requires a task ID and one or more frame numbers.
- Default quality is `original`; use `--quality compressed` for smaller sanity artifacts.
- Output naming is `task_<ID>_frame_<FRAME>.jpg`. Check `--outdir` and write permissions.
- A 404/permission error usually means wrong task ID, wrong organization, or insufficient token permissions.

## Auto-annotation and native function failures

Route implementation-level issues to `../../auto-annotation/SKILL.md`; use this CLI troubleshooting for command invocation problems.

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError` from `task auto-annotate` or `run-agent`. | The CLI does not add local directories to Python module search path. | Set `PYTHONPATH=path/to/project` or install the function package. |
| `function takes no parameters`. | `-p` was passed to a module object without a `create(...)` factory. | Remove `-p` or implement a `create` function that consumes parameters. |
| `function has no 'spec' attribute`. | Function module/object does not implement the auto-annotation protocol. | Add the required `spec` and method implementation; route to auto-annotation guidance. |
| `Unsupported function spec type`. | Native agent supports documented detection, interaction, and tracking specs; the supplied object used another spec. | Use a supported AA function spec. |
| Function provider/kind incompatibility. | The server-side native function metadata does not match the local function object used by `run-agent`. | Recreate the native function with the same local function, or run the matching function object. |
| Queue event stream repeatedly reconnects. | Server/network disruption or server version lacking the watch endpoint. | Keep the worker supervised, test `--burst`, and check server/API compatibility. |
| 429/rate-limit logs. | Server throttling. | Respect `Retry-After`; stagger agents rather than starting many workers at once. |

Native functions are Enterprise/Cloud-only. On community/self-hosted deployments without this feature, expect server-side 404/403/feature errors even when the local command syntax is valid.

## Version and compatibility checks

```bash
cvat-cli --version
python - <<'PY'
import importlib.metadata as md
print('cvat-cli', md.version('cvat-cli'))
print('cvat-sdk', md.version('cvat-sdk'))
PY
```

The CLI builds a SDK client and checks server version without failing on unsupported versions. If behavior differs from this skill, inspect the installed `cvat-cli --help` for the user's exact version and prefer the installed help over older examples.
