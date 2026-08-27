# Vaex CLI reference

This guide describes the public `vaex` console dispatcher and how to select a
small, safe diagnostic. Use the installed console entry point. If it is absent,
try `python -m vaex` in the same Python environment.

## Discovery sequence

```bash
vaex --help
vaex version
vaex open --help
vaex stat --help
vaex alias --help
vaex settings --help
vaex server --help
```

The top-level dispatcher in this Vaex line routes these commands:

| Command | What it does | Default safety / route |
| --- | --- | --- |
| `--help` | Prints the top-level command map | Read-only. |
| `version` | Prints Vaex package/build and Python information | Read-only. |
| `open` | Tries to open one or more inputs and returns a failure status if any fail | Read-only without `--delete`; prefer `--dry-run`. |
| `stat` | Opens one dataset and prints length, path, columns, descriptions, units, and dtypes | Read-only data inspection; use a local path unless remote access is approved. |
| `alias` | Lists, adds, or removes names used by Vaex openers | `list` is read-only; `add`/`remove` mutate aliases. |
| `settings` | Prints or persists effective configuration | Output commands are read-oriented; save/set/defaults write configuration. |
| `convert` | Opens/export datasets | Route semantics to [../io-conversion/SKILL.md](../../io-conversion/SKILL.md). Failed export cleanup can delete output unless `--no-delete` is used. |
| `server` / `webserver` | Starts a long-running service | Route to [../serving-remote/SKILL.md](../../serving-remote/SKILL.md); do not launch casually. |
| `benchmark` | Runs timing workloads over a dataset and expressions | Maintainer/expensive; not an install health check. |
| `test` | Runs Vaex's test entry point | Maintainer/expensive and environment-dependent; use a focused test request. |
| `meta` | Imports/exports dataset metadata | May write files or dataset metadata; inspect its help and obtain approval before mutation. |

The top-level help text in some releases contains a historical `veax` typo. It
does not change the command name.

## `open`: validate without deletion

```bash
vaex open --dry-run --verbose data.hdf5
status=$?
```

The parser accepts `--verbose`/`-v`, `--quiet`/`-q`, `--dry-run`/`-n`,
`--delete`, and zero or more inputs. It calls `vaex.open` for each input. A
successful check returns `0`; if an input raises an exception, the command
returns `123`. With `--delete`, a failed input is removed unless `--dry-run` is
also present. Therefore:

- Use `--dry-run --verbose` for a non-destructive failure report.
- Never combine `--delete` with an unreviewed path or wildcard.
- `--dry-run` prints the would-be removal only when `--delete` is present; it
  does not skip the open attempt.
- `--quiet` suppresses exception text, which is useful for automation but makes
  diagnosis harder.

A failing open can mean a missing file, unsupported format, missing optional
plugin, bad HDF5 group, or malformed input. Route format-specific diagnosis to
[../io-conversion/SKILL.md](../../io-conversion/SKILL.md).

## `stat`: compact metadata

```bash
vaex stat data.hdf5
vaex stat --fraction 0.1 data.hdf5
```

`--fraction` is a floating-point active fraction used for reporting. The
command prints dataset length/full length, name/path, and each visible column's
description, unit, and dtype. It does not export or rewrite the dataset, but it
must open the input and may invoke a plugin or filesystem backend.

## Aliases

```bash
vaex alias list
vaex alias add sample data.hdf5
vaex alias remove sample
```

Aliases are resolved by Vaex openers. The implementation writes the in-memory
alias map; depending on the package/settings integration, that mapping may be
persisted by later settings handling. Treat `add` and `remove` as state-changing
and ask before executing. `--force` is exposed by the parser, but do not rely on
special conflict behavior without checking the installed version. Never publish
an alias value that contains a private path.

## `settings` command map

```bash
vaex settings yaml
vaex settings json
vaex settings schema
vaex settings yaml-diff
vaex settings md
vaex settings
```

The first three are useful read-only diagnostics. `schema` is intended to emit
JSON schema; older/minimal builds can fail when their settings model lacks
`schema_json`. `yaml-diff` is intended to exclude defaults but can fail on
lightweight settings implementations. If either fails, use the bundled probe or
`vaex settings yaml/json` and record the exact version.

The following commands write state or developer files:

- `save`: writes non-default effective settings to the Vaex home YAML file.
- `set`: in this implementation also saves non-default settings; it is not a
  general `set KEY VALUE` parser.
- `save-defaults`: writes all defaults, which can include machine-specific
  paths and noisy values.
- `docgen`: rewrites a developer documentation file relative to the current
  source tree; do not run in a user project.
- `watch`: runs doc generation and waits for file changes; it is long-lived and
  requires the optional watchdog package.

## `convert` and `server` shallow routes

Use `vaex convert --help` and preserve `--no-delete` when diagnosing failed
exports. The conversion command's default failure cleanup can remove its output;
format choice, filters, chunking, column names, and validation belong to
[../io-conversion/SKILL.md](../../io-conversion/SKILL.md).

Use `vaex server --help` before any service command. A server command is a
long-running listener; host/port exposure, optional GraphQL, dataset aliases,
and local loopback validation belong to
[../serving-remote/SKILL.md](../../serving-remote/SKILL.md).

## Fallback and exit interpretation

```bash
if command -v vaex >/dev/null 2>&1; then
  vaex --help
else
  python -m vaex --help
fi
```

A missing console script with a working module usually indicates that the
package is importable but the environment's script directory is not on `PATH`.
A nonzero help/version result is an installation or optional-import problem;
collect stderr and package versions rather than retrying mutating commands.
