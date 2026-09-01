# `hf` CLI reference

This is a routing reference, not a promise that every installation has the
same surface. It was grounded in the 1.29.0 CLI source, English CLI/extension/
installation/package references, focused framework/output/error tests, and
live help from the supplied 1.29.0 environment. A different executable on
`PATH` may still select another version, so live `hf <path> --help` from the
intended environment always wins. Commands below use placeholders such as
`<namespace>/<repo>` and `<job-id>` so that copying an example cannot
accidentally target a real resource.

## Entry points and top-level routing

The package declares these console entry points:

- `hf` → the supported Click-based Hub CLI;
- `huggingface-cli` → deprecated compatibility entry point; current installs
  warn and exit rather than expose the old interface;
- `tiny-agents` → a separate MCP/agent command, not an `hf` alias; supplied
  1.29.0 live help exposes its `run` command, whose own help is authoritative.

Safe probes do not contact the Hub when the update check is disabled:

```bash
HF_HUB_DISABLE_UPDATE_CHECK=1 hf --help
HF_HUB_DISABLE_UPDATE_CHECK=1 hf version
HF_HUB_DISABLE_UPDATE_CHECK=1 hf --version
HF_HUB_DISABLE_UPDATE_CHECK=1 tiny-agents --help
```

The supported top-level groups confirmed by 1.29.0 live help are:

| Group | Route |
|---|---|
| `auth` | login, token selection, `whoami`, and logout |
| `buckets` | Xet-backed object storage, file listing, removal, copy, and sync |
| `cache` | local cache list, prune, remove, and checksum verification |
| `collections` | collection CRUD and item operations |
| `cp` | one-file local/Hub/bucket movement |
| `datasets` | dataset search, files, info, cards, parquet, SQL, leaderboard |
| `discussions` | discussions and pull requests |
| `download` / `upload` | repository file and snapshot transfer |
| `endpoints` | Inference Endpoints (the confirmed 1.29.0 group name) |
| `extensions` / `ext` | trusted third-party CLI extensions |
| `jobs` | hosted Jobs, schedules, logs, status, and hardware |
| `models` | model search, files, info, and cards |
| `papers` | Hub paper search, metadata, and Markdown |
| `repos` / `repo` | repository CRUD, settings, branches, tags, and files |
| `sandbox` | disposable/pooled machines, commands, processes, and file copy |
| `skills` | marketplace and generated agent skills |
| `spaces` | Space search, runtime, settings, secrets, variables, and volumes |
| `sync` | top-level alias for bucket sync |
| `webhooks` | webhook CRUD and state |

Also inspect `hf env`, `hf update`, and `hf version`. `upload-large-folder`
is retained but deprecated; use `hf upload`, which now handles large and
resumable folders. A hidden/internal `repo-files` and LFS helpers may appear in
some generated references but are not normal routing targets.

For a group or leaf catalog, use the same safe pattern:

```bash
HF_HUB_DISABLE_UPDATE_CHECK=1 hf <group> --help
HF_HUB_DISABLE_UPDATE_CHECK=1 hf <group> <command> --help
```

Unknown group/flag errors include available commands/options and sometimes a
fuzzy suggestion. Use that hint, then confirm the exact installed help rather
than guessing a spelling.

## Output contract

Most modern leaves accept the injected formatting options:

```text
--format auto|human|agent|json|quiet
--json                         equivalent to --format json
-q, --quiet                    equivalent to --format quiet
--no-truncate                  disable human scalar-cell truncation
```

`--format` can normally appear before or after leaf arguments because the CLI
consumes it while resolving a leaf. Do not assume that behavior for
`hf extensions exec`: it is a pass-through and forwards unknown arguments
unchanged. Some legacy leaves, notably `hf jobs ls`, own a local `--format`
option; the CLI rewrites compatible `--json`/`--quiet` shorthands for those
commands. Help for the leaf is authoritative.

| Mode | stdout contract | Typical use |
|---|---|---|
| `auto` | human in a terminal; agent when the environment is recognized as an agent | interactive default |
| `human` | colored/padded tables, pretty JSON for dicts, progress/status | people at a terminal |
| `agent` | untruncated TSV for tables, `key=value` for result summaries, compact JSON for dicts | agent/tool consumption without a schema |
| `json` | compact JSON arrays/dicts where the command emits structured output; free text may be suppressed | `jq`, Python, CI |
| `quiet` | the selected ID/result column, one per line; free text is suppressed | `xargs`, shell loops |

Empty tables print `No results found.` in human/agent, `[]` in JSON, and
nothing in quiet mode. Human tables may shorten values to fit the terminal;
use `--no-truncate` for display or JSON for reliable structure. Do not parse a
human table as a stable schema. A result summary in JSON contains data fields
and may omit its human message; inspect a representative result if the exact
schema matters.

Data is intended for stdout. Warnings, errors, update hints, skill hints, and
logging go to stderr in all modes (hints/logs are suppressed in quiet mode).
Progress bars and status lines are disabled outside human mode. Parse only
stdout, but preserve or relay stderr so a warning is not lost:

```bash
set -o pipefail
json=$(hf models ls --limit 2 --format json 2> >(tee /dev/stderr))
printf '%s\n' "$json" | jq -r '.[].id'
```

The exact process-substitution form is Bash-specific. In Python, use
`subprocess.run(..., capture_output=True, text=True)`, parse `result.stdout`,
and report `result.stderr` separately. A command's exit code, not a non-empty
stderr, determines success; warnings can accompany exit code 0.

Never use `hf auth token` as a generic probe: it deliberately prints the
current secret to stdout. Never combine JSON output with a binary stream such
as `hf cp <uri> -`.

## Authentication and token handling

Use an environment token in non-interactive shells:

```bash
export HF_TOKEN='read-from-a-secret-manager'
hf auth whoami --format json
```

`HF_TOKEN` takes precedence over the token stored on disk. `HF_TOKEN_PATH`
selects the stored-token path; `HF_HOME` controls the local Hub data root,
including the default token and cache locations. Set these before starting the
process. Do not echo them, use `set -x`, put them in a command committed to a
script, or print them in diagnostics. A shell-expanded `--token "$HF_TOKEN"`
works where an explicit option is required, but the environment form avoids
shell history and most argument logging:

```bash
HF_TOKEN="$TOKEN_FROM_SECRET_STORE" hf models info <namespace>/<model> --format json
```

`hf auth login` supports `--token`, `--add-to-git-credential`, and
`--force`. Browser/menu login is interactive. In agent mode it emits
instructions for the user and waits for device authorization; JSON and quiet
are not supported by the interactive flow, so use a token for automation.
`--add-to-git-credential` is a local credential-store mutation and should be
explicitly requested only when direct Git commands need it.

`hf auth list` (`ls`) lists token names, `hf auth switch` accepts
`--token-name` and optionally `--add-to-git-credential`, `hf auth logout`
accepts `--token-name`, and `hf auth whoami` verifies the active account. The
`hf auth token` command prints the active token; avoid using it in
scripts. If an approved downstream process genuinely requires the raw token,
use an ephemeral, masked secret channel and ensure neither stdout nor process
arguments are logged. Do not send it to an untrusted endpoint.

`HF_HUB_DISABLE_IMPLICIT_TOKEN`
can prevent read requests from automatically using the stored token, but may
hide private results; explicit authorization is then required.

For offline/read-mostly environments, `HF_HUB_OFFLINE=1` blocks Hub HTTP
requests and permits only cached reads. `HF_HUB_DISABLE_UPDATE_CHECK=1`
suppresses the startup PyPI and local `hf-cli` freshness hints. These
variables are read at import/startup time; set them before invoking `hf`.

## Repo types, revisions, and URIs

Repository commands accept the types `model`, `dataset`, and `space` through
`--type` or `--repo-type`. The default for most commands is `model`. Buckets
are not a repository type; use an `hf://buckets/...` URI with `cp`/`sync`.
For commands that accept a repository ID, a prefixed form such as
`spaces/<namespace>/<repo>` can infer the type. Do not combine an inferred URI
prefix with an explicit `--type`/`--repo-type`.

A canonical URI is:

```text
hf://[TYPE/]<namespace>/<name>[@<REVISION>][/<PATH>]
```

`datasets`, `spaces`, and `buckets` are the meaningful plural prefixes;
models may omit the prefix. A revision can be a branch, tag, commit hash, or
special ref such as `refs/pr/3`. A branch containing `/` must be URL-encoded
as `%2F` in a URI. A trailing `/` denotes a subfolder for download/copy
semantics. A URI carries its type/revision/path, so do not add duplicate
`--repo-type`, `--revision`, or a positional path where the command forbids
it.

Check a type/revision without mutating anything:

```bash
hf models info <namespace>/<model> --revision <branch-or-commit> --format json
hf datasets info <namespace>/<dataset> --revision <branch-or-commit> --format json
hf spaces info <namespace>/<space> --revision <branch-or-commit> --format json
```

## Downloads, uploads, copy, and sync

### `hf download`

Usage is `hf download REPO_ID [FILENAMES]...`. Confirm the leaf help for
these verified options:

- `--type/--repo-type model|dataset|space`, `--revision TEXT`;
- repeatable `--include TEXT` and `--exclude TEXT` glob patterns;
- `--cache-dir PATH` or `--local-dir PATH` (not both);
- `--force-download`, `--dry-run`, `--token TEXT`, and `--max-workers INTEGER`;
- common formatting options.

With one ordinary filename it uses the single-file path; otherwise it builds a
coherent snapshot. A filename ending in `/` means a subfolder. Explicit
filenames take precedence over include/exclude patterns, and subfolder
arguments cannot be combined with those patterns. A bucket URI is rejected by
`hf download`; use bucket sync/copy instead.

`--dry-run` performs metadata/listing work and reports each selected file,
size, cache state, and what would be transferred without downloading payloads.
It can still require network access and authorization. In JSON mode, parse
stdout as the dry-run array; human mode may include a summary/table and
stderr diagnostics. A dry run is not an offline inventory.

Safe preview examples:

```bash
hf download <namespace>/<model> --include '*.safetensors' --exclude '*.fp16.*' --dry-run --format json
hf download hf://datasets/<namespace>/<dataset>@<revision>/data/ --format json
hf download <namespace>/<model> config.json --local-dir ./scratch/model
```

The last example writes only under the chosen local scratch directory. For a
shared cache use `--cache-dir` or the `HF_HOME`/`HF_HUB_CACHE` configuration;
use `local-dir` when a normal materialized directory is required.

### `hf upload`

Usage is `hf upload REPO_ID [LOCAL_PATH] [PATH_IN_REPO]`. It can create a
missing repository, so treat it as a Hub mutation. Verified options include
`--type/--repo-type`, `--revision`, `--private`, repeatable `--include` and
`--exclude`, `--delete`, `--commit-message`, `--commit-description`,
`--create-pr`, `--every FLOAT`, `--token`, and output options. There is no
upload dry-run equivalent in this command. `--delete` removes matching remote
files while committing and deserves a separate review. `--create-pr` changes
the destination from a direct push to a pull request.

**Mutation example — run only after target, files, permission, and commit
intent are confirmed:**

```bash
# MUTATION: uploads local files; never run with a placeholder target.
hf upload <namespace>/<repo> ./reviewed-files /incoming \
  --repo-type model --exclude '*.secret' --commit-message 'Reviewed upload'
```

`upload-large-folder` is deprecated; route new workflows through `hf upload`.

### `hf cp`

`hf cp SRC [DST]` moves one file between a local file, an `hf://` repository
or bucket URI, and `-` for stdin/stdout. The same implementation is exposed as
`hf repos cp` and `hf buckets cp`; the prefixed aliases reject the wrong remote
kind. It does not support local-to-local, stdin-to-local, directory transfers
with a local side, or bucket-to-repository copies. Remote-to-remote copies
must be in the same storage region. A destination ending in `/` uses the
source basename for file uploads; a remote source ending in `/` means a
folder-like remote copy and should be handled carefully.

`-` is a byte stream, not a formatting stream:

```bash
hf cp hf://datasets/<namespace>/<dataset>/config.json - > ./config.json
# MUTATION: uploads stdin to the approved bucket destination.
cat ./config.json | hf cp - hf://buckets/<namespace>/<bucket>/config.json
```

The second line is a mutation and requires authorization; the first is a
read-only download. Use `hf download`/`hf upload` for repository directories
and `hf sync` for local↔bucket directories.

### `hf sync` and `hf buckets sync`

`hf sync [SOURCE] [DEST]` is the top-level alias of the bucket sync command.
Both endpoints are a local directory or a bucket URI. Verified controls are:

- `--delete`, `--ignore-times`, `--ignore-sizes`;
- `--plan FILE`, `--apply FILE`, and `--dry-run`;
- repeatable `--include`, `--exclude`, `--filter-from`;
- `--existing`, `--ignore-existing`, `-v/--verbose`, and `--token`.

`--dry-run` prints JSONL to stdout without executing transfers. `--plan FILE`
saves a plan for review and does not execute it; `--apply FILE` executes a
previous plan and is a mutation. Review paths, operation types, filters,
deletes, and the plan's intended bucket before applying. A plan is not a
permission grant and can become stale.

Safe preview:

```bash
hf sync ./scratch/data hf://buckets/<namespace>/<bucket> \
  --include '*.safetensors' --exclude '*.tmp' --dry-run | jq .
```

**Mutation example — apply only after reviewing the JSONL plan and confirming
that its source, destination, and delete set are still correct:**

```bash
# MUTATION: executes remote/local transfers described by this file.
hf sync --apply ./reviewed-sync-plan.jsonl
```

## Repositories, branches, tags, and catalog browsing

### `hf repos` / `hf repo`

The group supports `branch`, `cp`, `create`, `delete`, `delete-files`,
`duplicate`, `list/ls`, `move`, `settings`, and `tag`. `repos list` can filter
by repo type/namespace/search and emits machine-readable IDs with
`--format json` or `-q`; confirm its leaf help for the installed release.
Branch and tag subgroups use `create`, `delete`, and `list/ls` (tags). Common
verified controls are `--repo-type/--type`, `--revision`, `--token`, and
`--exist-ok` where creation supports it. Tag deletion and repository deletion
support `-y/--yes`.

**Mutation example — confirmation is intentionally omitted so the command
stops at the destructive gate:**

```bash
hf repos delete <namespace>/<repo> --repo-type model
```

The command is irreversible and must be explicitly confirmed in human mode or
passed `--yes` only after an automation review. In non-human modes the CLI's
confirmation helper raises a confirmation error unless the command receives
its `--yes` flag. `delete-files` is a commit mutation; quote shell globs so
your shell does not expand them:

```bash
# MUTATION: deletes matching remote files or creates a PR; inspect the pattern first.
hf repos delete-files <namespace>/<repo> '*.tmp' --repo-type model --create-pr
```

### Models, datasets, Spaces, papers, collections

These are primarily read/search routes. The `list` command is also an alias
`ls`, and with a repo ID it lists files instead of catalog items.

- `hf models list/ls`: `--search`, `--author`, repeatable `--filter`,
  `--pipeline-tag`, `--gated/--no-gated`, `--apps`, `--num-parameters`,
  `--inference-provider`, `--warm`, `--sort`, `--limit`, `--expand`,
  `--revision`, plus `--human-readable`, `--tree`, `-R/--recursive`, and
  `--token`.
- `hf models info MODEL_ID`: `--revision`, `--expand`, `--token`.
- `hf models card MODEL_ID`: `--metadata`, `--text`, `--token`.
- `hf datasets list/ls`: `--search`, `--author`, repeatable `--filter`,
  `--sort`, `--limit`, `--expand`, file-listing `--human-readable`,
  `--tree`, `-R/--recursive`, `--revision`, `--token`.
- `hf datasets info DATASET_ID`: `--revision`, `--expand`, `--token`.
- `hf datasets card DATASET_ID`: `--metadata`, `--text`, `--token`.
- `hf datasets leaderboard DATASET_ID`: `--limit`, `--token`.
- `hf datasets parquet DATASET_ID`: `--subset`, `--split`, `--token`.
- `hf datasets sql SQL`: `--token`; the query is executed against parquet
  URLs with the optional DuckDB dependency and should be treated as networked
  read work.
- `hf spaces list/ls`: `--search`, `--author`, repeatable `--filter`,
  `--sort`, `--limit`, `--expand`, file-listing `--human-readable`,
  `--tree`, `-R/--recursive`, `--revision`, `--token`.
- `hf spaces info SPACE_ID` and `hf spaces card SPACE_ID` support revision or
  card `--metadata/--text` as applicable, plus `--expand`/`--token`.
- `hf papers list/ls`, `search`, `info`, and `read` cover daily lists, query,
  arXiv metadata, and Markdown; inspect each leaf for date/limit flags.
- `hf collections` covers list/info/create/update/delete and item add/update/
  delete operations; creation and updates are mutations.

Safe catalog examples:

```bash
hf models ls --search '<term>' --limit 5 --format json | jq -r '.[].id'
hf datasets ls --filter '<tag>' --limit 5 --format json
hf spaces card <namespace>/<space> --metadata --format json
hf papers search '<term>' --limit 5 --format json
```

Space runtime commands such as `pause`, `restart`, `settings`, `dev-mode`,
`hot-reload`, secrets/variables, volumes, and `ssh` can change remote state or
open an interactive session. `spaces wait SPACE_ID --timeout 5m` is a useful
status gate: it exits 0 only when the Space is running and non-zero for a
settled error state. `secrets ls` never returns secret values, but variables
are readable. Treat `secrets add/delete` and all settings/volume mutations as
explicitly authorized operations.

## Discussions and webhooks

`hf discussions` provides `list/ls`, `info`, `create`, `comment`, `edit`,
`close`, `reopen`, `merge`, `rename`, and `diff`. List supports
`--status open|closed|merged|draft|all`, `--kind all|discussion|pull_request`,
`--author`, `--limit`, `--repo-type/--type`, and `--token`. Creation supports
`--title`, `--body` or `--body-file`, and `--pull-request/--pr`. Close and
merge have `--comment` and `-y/--yes`; reopen also has a confirmation gate.
Use JSON for listing/info, and treat create/comment/edit/close/reopen/merge as
mutations.

`hf webhooks` provides `list/ls`, `info`, `create`, `update`, `enable`,
`disable`, and `delete`. Creation requires repeatable `--watch TYPE:NAME` and
one of `--url` or `--job-id`, optionally repeatable `--domain repo|discussions`
and `--secret`. Delete has `-y/--yes`. Webhook secrets should come from a
secret manager and must not be written to shell history or logs.

**Mutation examples — run only with a confirmed target and destination:**

```bash
# MUTATION: creates a discussion.
hf discussions create <namespace>/<repo> --title 'Issue title' --body 'Reviewed details.'
# MUTATION: creates a webhook pointing at the approved endpoint.
hf webhooks create --url https://hooks.example.invalid/receiver \
  --watch model:<namespace>/<model> --domain repo
```

## Buckets, Jobs, and sandboxes

Buckets are mutable object storage, not Git repositories. `hf buckets` has
`create`, `delete`, `info`, `list/ls`, `move`, `remove/rm`, `settings`,
`sync`, and `cp`. `list` accepts a namespace for bucket listing or a bucket
ID/prefix for object listing; `-R/--recursive`, `--tree`, and `-h/--human-readable`
control file display. `remove` supports `-R/--recursive`, `--include`,
`--exclude`, `--dry-run`, and `-y/--yes`. `delete` and settings are remote
mutations; removal and move are mutations too.

`hf jobs` has `run`, `list/ls/ps`, `inspect`, `logs`, `wait`, `cancel`,
`stats`, `labels`, `hardware`, `ssh`, `uv run`, and `scheduled` subcommands.
Important verified controls:

- `jobs run IMAGE COMMAND...`: `-e/--env`, `-s/--secrets`, `--name`,
  repeatable `-l/--label`, repeatable `-v/--volume`, env/secrets files,
  `--flavor`, `--timeout`, `-d/--detach`, repeatable `--expose`, `--ssh`,
  `--resource-group-id`, `--namespace`, and `--token`.
- `jobs ls`: `-a/--all`, repeatable/comma-separated `--status`, repeatable
  `-l/--label`, `--name`, `--limit` (0 means no limit), `--namespace`, and
  deprecated `-f/--filter`.
- `jobs logs`: `-f/--follow`, `-n/--tail`, namespace, token. Following logs
  ends when the stream ends regardless of job success.
- `jobs wait JOB_IDS...`: `--timeout`, namespace, token. It exits 0 only if
  every job completes successfully; all IDs must share a namespace.
- `jobs uv run SCRIPT [SCRIPT_ARGS]...`: image, flavor, env/secrets, name,
  labels, volumes, files, timeout, detach, expose, SSH, namespace/token,
  repeatable `--with`, and `-p/--python`.
- `jobs scheduled` provides schedule run/list/inspect/labels/suspend/resume/
  trigger/delete and scheduled UV runs. Treat run/trigger/resume/label/delete
  as mutations and inspect schedule syntax with help.

A local directory volume is first synced to a bucket. Models, datasets, and
Spaces mount read-only; buckets are read-write by default, so check `:ro` or
`:rw` explicitly. Never pass a secret as a regular `--env` value.

Sandboxes are Jobs-backed disposable machines. `hf sandbox create [IMAGE]`
accepts `--pool`, `--flavor`, `--idle-timeout`, env/secrets files, volumes,
namespace, `--forward-hf-token`, and token. `exec` streams a command and
propagates its exit code; `spawn` starts a background process; `process ls`
and `process kill` inspect/stop it; `cp` moves one file docker-style; `kill`
terminates a sandbox/host and supports `--all` and `-y/--yes`; `pool create`
warm-starts a host pool. These all incur remote effects or cost except
read-only help/status, so require an explicit compute request.

## Extensions and generated agent skills

### Extensions

Extensions are third-party executables or Python packages. Install only from
a source you trust. `hf extensions` (alias `ext`) provides:

- `install [OWNER/]hf-<name> [--force]` — fetches from a public GitHub repo;
- `list/ls` — lists installed commands;
- `search` — searches GitHub repositories tagged `hf-extension`;
- `update [NAME]` — updates one installed extension or checks all installed;
- `remove/rm NAME` — removes an installed extension;
- `exec NAME [-- forwarded-args]` — runs an installed extension.

A shell extension is an executable root file named `hf-<name>`. A Python
extension is a package whose project script exposes the same `hf-<name>`
console script. Names use letters, digits, `.`, `_`, and `-`, cannot contain
path traversal, and cannot collide with a built-in command. A root
`manifest.json` can provide a description. Python extensions are installed in
an isolated extension virtual environment. `--force` replaces an install and
should be used only after checking the repository and intended version.

**Mutation example — install only an audited/trusted repository:**

```bash
# MUTATION: downloads and may execute/install third-party code.
hf extensions install <owner>/hf-<name>
```

For development, `hf extensions exec <name> -- --help` passes arguments through
unchanged. Global format flags are not rewritten for this pass-through path.
An installed extension can also be dispatched as `hf <name>`, but a mistyped
unknown top-level name may trigger an official-extension existence check and a
human confirmation flow; use the explicit `extensions` group in automation.

### `hf skills`

The 1.29.0 source and live help expose `add`, `list/ls`, `preview`, and
`update`; they do **not** expose an explicit `hf skills check` subcommand. If a
user requests
“check skills”, first run `hf skills --help` and distinguish these two cases:

1. The CLI's implicit startup checker runs at most once per 24 hours, locally.
   It only writes a timestamp and emits a stderr hint when `hf-cli` is missing
   or generated by another version; it never installs or updates files. It is
   skipped for `hf skills ...` and `hf update`, and
   `HF_HUB_DISABLE_UPDATE_CHECK=1` disables it.
2. A deliberate refresh is `hf skills update`, which can rewrite managed
   skill files and may contact the marketplace. It is a mutation.

`hf skills add [NAME]` installs the default generated `hf-cli` skill locally
from the running CLI, or downloads another marketplace skill. Verified options
are `--claude`, `-g/--global`, `--dest PATH`, and `--force`. Without flags it
uses the current project's `.agents/skills`; `--global` uses the user-level
skills directory. `--claude` also links/copies to the Claude skills location.
`--dest` is a custom skills root and cannot be combined with `--claude` or
`--global`. Existing content requires `--force`.

`hf skills list` queries the marketplace and reports project/global install
locations. `hf skills preview` prints only the generated `hf-cli/SKILL.md` to
stdout and is the safest way to inspect target content. `hf skills update
[NAME]` updates managed generated/marketplace installs; it accepts the same
scope selectors `--claude`, `-g/--global`, and `--dest PATH`. Unmanaged skill
directories are reported rather than silently treated as managed.

**Mutation example — writes a target-side agent skill, not this repo skill:**

```bash
# MUTATION: creates/updates files under the selected destination.
hf skills add --dest ./scratch/agent-skills
```

This generated target-side `hf-cli/SKILL.md` is a different artifact from
this repo's managed `skills/huggingface-hub/sub-skills/cli-and-automation/`
directory. Do not use `hf skills add`, `update`, or `--force` in examples as a
way to modify the latter. Preview instead:

```bash
hf skills preview > ./scratch/generated-hf-cli-SKILL.md
```

The preview command is local-only; review the destination before retaining
that file. Never claim that `hf skills check` is available when live help says
otherwise.

## Read-only environment and cache routes

`hf env` prints diagnostic environment information. It is safe but may reveal
paths or versions, so redact it before sharing. `hf cache list/ls` inspects
cached repositories/revisions; `cache prune`, `cache rm`, and cache verify
have their own help and deletion/verification semantics. Use `--dry-run` and
`--yes` gates where offered, and keep `HF_HOME`, `HF_HUB_CACHE`, timeouts,
offline, verbosity, and Xet settings in the environment reference rather than
hard-coding machine paths.
