# CLI API/framework and output internals

Use this reference to explain behavior observed at the command boundary. It
covers the public-for-this-repo CLI conventions and the CLI-to-Hub-API boundary,
not a promise that internal Python helpers are a stable external API. Prefer
`hf ... --help` and the high-level Python APIs for new integrations.

## CLI-to-Hub-API boundary

Leaf commands validate and confirm first, then obtain an `HfApi` client through
the shared CLI helper with the selected token. Known Hub and CLI exceptions are
formatted once at the root; command implementations should not catch and hide
repository, revision, authorization, or validation errors merely to rewrite
them. This ordering is safety-significant: for example, repository deletion
calls the confirmation sink before constructing the API client, so refusal can
be asserted to make zero delete calls.

Use CLI output as an automation interface only where the leaf exposes a stable
structured mode. If a workflow needs richer pagination, typed objects, custom
retry behavior, or composition without subprocess parsing, route to the
corresponding high-level Python API rather than importing private CLI modules.

## Command declaration model

The CLI is built on Click through a small compatibility layer in
`huggingface_hub.cli._framework` and `_cli_utils`. Command functions use
annotated `Argument` and `Option` markers. The framework converts:

- `str`, `int`, `float`, `Path`, string-valued enums, and `Literal` choices to
  Click parameter types;
- `T | None` to an optional parameter;
- `list[T]` options to repeatable options and list arguments to variadic
  positional arguments;
- Python booleans to `--flag/--no-flag`, unless the command declares a single
  explicit flag such as `--yes` or `--metadata`;
- underscore names to kebab-case defaults, for example `force_download` to
  `--force-download`.

Pipe-separated declarations create aliases. This is why `list | ls`,
`repos | repo`, `extensions | ext`, and `remove | rm` appear together in help.
The main group keeps sectioned help and enriches unknown-command/unknown-option
errors with available names or options.

The root callback accepts eager version/completion options. `--help` is safe
and should be preferred over introspecting private Click objects in an
automation script.

## Formatting dispatch

The singleton output sink resolves `auto` from the terminal/agent detector and
can be overridden by the global formatter preprocessor. For modern leaf
commands, the preprocessor removes `--format`, `--json`, `-q/--quiet`, and
`--no-truncate` before Click parses command parameters, then configures the
sink. It rejects multiple output selectors, for example `--json` together
with `--format human`, and rejects `--format` without a value or with an
unknown enum value.

A pass-through command with `ignore_unknown_options` is not preprocessed;
`hf extensions exec` therefore forwards `--json`, `--format`, and arbitrary
extension flags to the extension. A legacy command with its own formatter,
such as `hf jobs ls`, retains its local grammar and receives compatible
shorthand rewrites.

The output sink's observable operations are:

| Operation | human | agent | json | quiet |
|---|---|---|---|---|
| table | padded/adaptive table, uppercase headers | header + TSV rows | compact JSON array | `id_key` or first column per line |
| dict | indented JSON | compact JSON | compact JSON | JSON unless a command supplies a quiet ID key |
| result | checkmark/message + fields | space-separated `key=value` | data object; message omitted | first data value |
| text | free text | agent-specific text | suppressed | suppressed |
| empty table | `No results found.` | `No results found.` | `[]` | empty |

Human table cells can be shortened to fit terminal width. `--no-truncate`
disables scalar truncation but does not turn nested list/dict values into a
stable schema. Agent cells are untruncated TSV; timestamps are full ISO values.

## Stream and status rules

The output implementation flushes output eagerly because device-code login
must be visible while waiting. `warning`, `error`, `log`, and `hint` write to
stderr in every mode; `log` and `hint` are suppressed in quiet mode. Human
status/progress lines are disabled in non-human modes. This separation is why
`json.loads(stdout)` is the correct parser even when stderr contains a
warning or hint.

Exceptions are handled by the root entry point. Known Hub/CLI errors are
rendered as an `Error:` line to stderr, optionally followed by a hint to set
`HF_DEBUG=1`; the process exits non-zero. With `HF_DEBUG=1`, a traceback is
also printed for debugging. Do not use debug mode in a secret-bearing CI log.

The confirmation helper has a strict non-human behavior: without a truthy
`--yes` value it prompts only in human mode and raises `ConfirmationError` in
agent, JSON, or quiet mode. Commands expose this as `-y/--yes` where the
operation is destructive. A wrapper should treat a non-zero refusal as
successfully prevented, not retry with `--yes`.

## Shared argument conventions

CLI utility aliases centralize common parameter declarations:

- token options accept a User Access Token and normally use `HF_TOKEN` instead;
- repo type options expose `--type` and `--repo-type` with model/dataset/space
  choices where applicable;
- revision options accept a branch, tag, commit hash, or special ref;
- repeated list options are passed once per value, for example
  `--include '*.json' --include '*.jsonl'`;
- volume options use `-v/--volume` and a mount grammar documented in the
  Jobs/Sandbox help.

The CLI rewrites repository-ID prefixes only for commands with a matching
repo-type option and repo-ID argument. Thus `spaces/<org>/<name>` can become
`<org>/<name> --type space`; combining that prefix with an explicit type is an
ambiguity error. This rewrite does not apply to arbitrary filenames or paths.

## URI and file-stream boundary

`parse_hf_uri` recognizes the `hf://` scheme and separates endpoint type,
repository/bucket ID, revision, and path. `hf cp` uses the parsed URI to
select one of download, upload, stdin/stdout, or remote-to-remote copy. The
special `-` endpoint bypasses the output formatter and carries raw bytes.
Therefore:

- do not parse `hf cp ... -` as JSON unless the remote file itself is JSON;
- use a full destination filename for stdin uploads;
- directories require `hf upload`/`hf download` or `hf sync`;
- `hf repos cp` and `hf buckets cp` add a remote-kind guard around the shared
  implementation.

## Generated CLI skill implementation

`hf skills preview` calls the local command registry to render a generated
`hf-cli/SKILL.md`. It includes leaf signatures, flags, common formatting
options, and examples from the currently running CLI. The output is a
snapshot, not this repository's `cli-and-automation` sub-skill.

The generated `hf-cli` skill is version-stamped. The startup checker compares
that stamp with the running package version at most once per 24 hours and only
emits a stderr hint. `hf skills update` regenerates the default skill or
refreshes managed marketplace skills; it is the explicit write operation.

## Evidence-backed maintenance checks

When CLI internals change, inspect these behaviors rather than relying on a
single command test:

1. `hf <leaf> --help` has one argument/options layout and the expected global
   formatter section.
2. `--format json`, `--json`, `--format agent`, and `--quiet` select the
   intended stream without changing pass-through extension arguments.
3. warnings/errors/hints remain on stderr and structured payloads stay valid on
   stdout.
4. destructive confirmation refuses non-human invocations without `--yes`.
5. URI type-prefix rewrites reject conflicting explicit types.
6. generated skill preview reflects the current command registry.

The repository's framework/output tests exercise these units, but a subprocess
fixture is still needed to prove actual shell stream and exit-code behavior.
