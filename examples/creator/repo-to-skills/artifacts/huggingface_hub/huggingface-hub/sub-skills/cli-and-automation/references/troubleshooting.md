# CLI troubleshooting

Start with a safe, version-pinned diagnosis. Do not paste tokens or full
secret-bearing environments into an issue or log.

## Command not found or old entry point

**Symptoms:** `hf: command not found`, an unexpected command catalog, or
`huggingface-cli` prints a deprecation warning and exits.

1. Run `command -v hf`, `command -v huggingface-cli`, and `command -v
   tiny-agents`.
2. Run `hf version` and `python -c "import huggingface_hub; print(huggingface_hub.__version__)"`
   from the intended environment.
3. Compare the executable's install location with the intended Python
   environment. A shell PATH can select a different wheel.
4. Use the supported `hf` entry point. `huggingface-cli` is not a repair path;
   update the package or standalone CLI through its documented installer.
5. Run `hf --help` after changing PATH. Avoid piping a network installer into
   an unreviewed environment; host-mutating installers are outside this skill.

The package supports Python 3.10+. Optional extras may be needed for specific
features such as DuckDB-backed dataset SQL or MCP-related commands, but they
are not required for the core CLI.

## Invalid group, command, or flag

**Symptoms:** “No such command”, “No such option”, or an option that worked in
another environment fails.

1. Capture `command -v hf`, `hf --version`, and the failing argv without secrets.
2. Run `HF_HUB_DISABLE_UPDATE_CHECK=1 hf --help`, then the nearest group and
   leaf help from that same executable.
3. Compare the requested path and flags with live help. If a source checkout,
   generated reference, wrapper, or another shell shows a different version,
   classify this as version skew rather than retrying guessed spellings.
4. Use an installed alias or replacement only when live help shows it. If the
   command is unsupported, stop without mutation and either use a documented
   command from this version or deliberately upgrade through the operator's
   package-management policy.

Additional checks:

- Use aliases actually shown by help (`repos`/`repo`, `extensions`/`ext`,
  `list`/`ls`, `remove`/`rm`, and `jobs list`/`ls`/`ps` where applicable).
- Inspect the exact leaf help; the root catalog is not a complete option list.
- Do not use `--format table`: the supported values are `auto`, `human`,
  `agent`, `json`, and `quiet`.
- Do not pass `--json` and `--format ...` together; formatting selectors are
  mutually exclusive.
- Remember that `hf extensions exec` passes unknown flags to the extension;
  its error may belong to the extension, not `hf`.
- If a source checkout and installed wheel disagree, report both versions,
  paths, the unsupported command/flag, and the nearest supported route; follow
  the selected executable's help. Do not silently run `hf update`, an installer,
  or a fallback mutation.

## JSON/quiet parsing failures

**Symptoms:** `json.loads` or `jq` sees a warning, progress bar, table header,
or empty output.

- Parse stdout only. Warnings, hints, errors, and normal logs are stderr.
- Set `--format json` explicitly for a structured command. `--format agent`
  is TSV, not JSON.
- `--quiet` prints an ID/result field one per line and suppresses free text;
  it is not a general “less verbose” mode.
- Set `HF_HUB_DISABLE_UPDATE_CHECK=1` in a strict help/CI probe to suppress
  startup update and skill hints. Preserve stderr separately rather than
  blindly discarding it.
- Check the exit code before parsing. A command can succeed with a warning;
  do not fail merely because stderr is non-empty unless your policy requires it.
- `hf cp ... -` is a raw byte stream and bypasses formatting. If the file is
  JSON, capture it as bytes/text and parse that file, not CLI output metadata.
- For card/read/paper text commands, the payload is free text rather than a
  JSON table even if a formatting flag is accepted; use a metadata mode where
  available.

## Token leakage or authentication state

**Symptoms:** unauthorized/private access, a token in logs, or an account
that differs between shells.

- Prefer `HF_TOKEN` from a masked secret store. It overrides stored token
  state. Avoid `set -x`, `env` dumps, command history, URLs containing tokens,
  and printing `hf auth token`.
- Use `hf auth whoami --format json` as an account check; it does not prove
  access to every private or gated repository.
- Use `hf auth list` to see token names and `hf auth switch --token-name NAME`
  to choose one. `hf auth logout --token-name NAME` removes one stored token.
- `HF_TOKEN_PATH` and `HF_HOME` change where local auth state is read/written;
  set them before starting the process. `HF_TOKEN` does not mean that
  `hf auth logout` can remove the environment token; unset it in the caller.
- For Git commands, request `--add-to-git-credential` explicitly and verify
  the configured credential helper. Do not add it just to suppress a prompt.
- A gated repository may require approval in addition to a valid token. A
  private repository may require repository permission. Neither is fixed by
  changing output mode.
- `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` can hide private results in read calls;
  provide explicit authorization when that privacy setting is intentional.

## Confirmation refusal and destructive commands

**Symptoms:** a command aborts in CI/non-human mode or a test unexpectedly
would delete/mutate.

- Deletion, removal, close/merge, webhook deletion, secret deletion, and some
  resource operations intentionally confirm. Human mode prompts; agent/json/
  quiet mode refuses without `-y/--yes`.
- Treat non-zero confirmation refusal as the desired safe outcome. Never retry
  automatically with `--yes`.
- `--yes` is only a prompt bypass; it does not validate the target, permission,
  plan freshness, or backup. Use it only after a separate approval record.
- For `hf repos delete`, check the exact repo type and target; it is
  irreversible. For `delete-files`, quote globs so the local shell does not
  change the selected pattern.
- `hf buckets rm --dry-run`, cache deletion dry runs, `hf download --dry-run`,
  and `hf sync --plan/--dry-run` are previews, not universal support for every
  mutation command. Confirm leaf help.

## Repo type, revision, path, and URI mistakes

**Symptoms:** wrong repository kind, revision not found, files selected from
the wrong path, or a bucket passed to a repository command.

- Use `--repo-type dataset` or `--type space` where supported; model is often
  the default. Buckets use `hf://buckets/<namespace>/<bucket>` and are not a
  `--repo-type` choice.
- Use one source of truth: either a plain repo ID plus `--repo-type` and
  `--revision`, or an `hf://` URI carrying type/revision/path. Do not combine
  them when the command rejects duplicates.
- Encode a branch slash as `%2F` in URI revisions. Keep `refs/pr/N` intact.
- A trailing slash means subfolder-like behavior for downloads/copies; it can
  change whether a directory itself or only its contents are nested.
- `hf download` does not accept bucket URIs; use `hf sync` or `hf cp`.
- `hf cp` requires a file when a local side is involved. Use `hf upload` or
  `hf download` for repo directories and `hf sync` for bucket directories.
- Remote-to-remote copy is region-constrained; bucket-to-repo and local-to-
  local copy are unsupported.
- For `hf://` mount specs, distinguish the remote path from the local mount
  path and access suffix (`:ro`/`:rw`). Do not improvise by splitting a URI
  on every colon.

## Plan/apply and sync conflicts

**Symptoms:** a plan applies different actions than expected, `--apply` rejects
arguments, or an intended sync deletes files.

1. Generate a JSONL plan with the exact source/destination, filters, revision,
   and account.
2. Inspect every action and deletion, including include/exclude precedence.
3. Recheck the source and destination immediately before applying; plans can
   become stale.
4. Use `--existing` or `--ignore-existing` for one-sided update policy.
5. Apply only the reviewed file with `hf sync --apply PLAN`; do not combine
   it with a new source/destination unless leaf help explicitly permits it.
6. Treat `--delete` as destructive and require a separate approval.

For `hf download --dry-run`, metadata requests can fail offline or for a
private/gated target; that does not indicate that the dry-run flag transferred
payloads. For a failed transfer, inspect disk/cache space and timeout settings
before retrying.

## Network, timeout, and offline errors

**Symptoms:** connection timeout, rate limit, CDN failure, or offline-mode
exception.

- Preserve the exit status and stderr request/error message. Retry only
  idempotent reads with bounded backoff; do not blindly retry mutations.
- `HF_HUB_ETAG_TIMEOUT` controls metadata lookup timeout and
  `HF_HUB_DOWNLOAD_TIMEOUT` controls payload download timeout. Set them before
  process startup when a slow connection warrants it.
- `HF_HUB_OFFLINE=1` blocks HTTP calls and uses only cached files. It is not a
  way to preview an uncached remote plan.
- `HF_HUB_DISABLE_UPDATE_CHECK=1` prevents startup version/skill hints from
  making a help/CI probe network-dependent.
- Check `hf env` or `HF_DEBUG=1` only in a redacted, private diagnostic run;
  debug mode logs request-equivalent cURL details and can expose URLs/headers.
- Extension GitHub search/install/update has separate network/rate-limit
  failures. A GitHub rate limit is not evidence that an extension repository
  is missing; wait or authenticate according to the supported flow.

## Extension trust, update, and dispatch failures

**Symptoms:** install rejects a repository, the command is missing, a Python
extension has no executable, or update says it is unavailable.

- The repo must be public and named `hf-<name>` (optionally with an owner).
  Names allow letters, digits, `.`, `_`, and `-`; built-in command collisions
  are rejected.
- Inspect the source before `hf extensions install`; it downloads and may
  execute a shell binary or install a Python package with dependencies.
- A shell extension needs an executable root `hf-<name>` file. A Python
  extension must expose that console script through its package metadata.
- Use `hf extensions list` to inspect installed manifests and
  `hf extensions exec NAME -- --help` to pass help to the extension. The
  explicit `exec` route avoids mistaking an unknown top-level command for a
  typo/official extension dispatch.
- `--force` reinstalls; use it only after validating the source and accepting
  replacement. `update NAME` requires an installed extension; no-name update
  checks all installed extensions and may skip individual failures.
- If GitHub is unreachable or rate-limited, do not convert the error to “not
  found”; retry later and preserve the diagnostic.

## Skills generation/update drift

**Symptoms:** `hf skills check` fails, `hf-cli` is stale, or target-side skill
files are confused with this repository skill.

- There is no explicit `hf skills check` command in the checked source. Run
  `hf skills --help` to verify the installed version.
- Startup checking is advisory, local, and at most daily. It compares the
  version stamp in an installed `hf-cli/SKILL.md`, prints a stderr hint, and
  never installs/updates. It skips the `skills` and `update` top-level routes.
- `hf skills preview` is a read-only generated snapshot to stdout.
  `hf skills add` and `hf skills update` write target-side agent skill roots;
  `--force` overwrites an existing target install. `--dest` cannot be combined
  with `--global`/`--claude`.
- Do not edit or delete this repo's managed sub-skill to repair a target-side
  generated skill. Use the explicit target-side command after reviewing the
  destination. Set `HF_HUB_DISABLE_UPDATE_CHECK=1` in offline CI if advisory
  hints are unwanted.

## Generated docs/static-import drift

**Symptoms:** generated CLI reference, static imports, or `__all__` checks fail.

- Compare the live leaf help with the generated page and command source.
- Regenerate through the maintainer workflow, do not hand-edit generated
  output as the final fix.
- Run `make style` then `make quality` in a controlled checkout and review all
  changed generated files. If only a user-facing `hf` runtime question is
  involved, report the installed help/version instead of running maintainers'
  generators.
- Keep source-side generator paths out of published runtime links; this skill
  contains only the safe help checker.
