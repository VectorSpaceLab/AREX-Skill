# CLI and settings troubleshooting

Begin with a non-mutating fact capture:

```bash
vaex --help
vaex version
vaex settings yaml
python scripts/vaex_cli_smoke.py --json
python scripts/vaex_settings_probe.py --pretty
```

Keep raw output private when it contains home, cache, lock, data, alias, or
filesystem paths. Summarize the relevant field names and error messages instead
of copying machine-specific values into shared artifacts.

## Console command missing

Symptoms:

- `vaex: command not found`.
- `python -m vaex --help` works but the `vaex` command does not.
- `vaex version` imports a different package version than the active Python.

Actions:

1. Run `python -m vaex --help` from the Python environment expected to contain
   Vaex.
2. In Python, run:

   ```python
   import vaex
   print(getattr(vaex, "__version__", "unknown"))
   ```

3. If module execution works but the script is missing, fix the environment's
   script directory/activation or reinstall the public package entry points.
4. If import fails, install the needed public Vaex distribution set for the
   task. CLI/settings require `vaex-core`; server routes additionally need the
   server package.

Do not rely on a repository launcher script as proof that the installed package
entry point is usable.

## Help or optional command import fails

The top-level dispatcher imports optional packages lazily. `vaex server --help`
can fail when the server package or a server dependency is absent even though
`vaex --help` works. `vaex benchmark` and `vaex test` are also not minimal
health checks.

Actions:

- Confirm whether the task actually needs the optional command.
- For server behavior, route to [../serving-remote/SKILL.md](../../serving-remote/SKILL.md).
- For conversion behavior, route to [../io-conversion/SKILL.md](../../io-conversion/SKILL.md).
- Use `vaex version`, `vaex settings yaml`, and a tiny `open --dry-run` fixture
  before escalating to tests or benchmarks.

## `vaex open` returns 123

`123` means at least one input could not be opened. The command may still have
successfully opened other inputs. Typical causes are missing files, unsupported
format, missing plugins, bad HDF5 group, bad CSV/schema, or unauthorized remote
paths.

Safe next steps:

```bash
vaex open --dry-run --verbose candidate.hdf5
```

- Do not add `--delete` unless the user explicitly asks to remove failed input
  files and has reviewed an allowlist.
- If a glob expands to many files, print or log the exact list before any
  destructive command.
- If the target is remote or credentialed, ask before running a networked open
  check.
- Use `vaex stat` only after the open path is understood; it must open the
  dataset too.

Format-specific diagnosis belongs in
[../io-conversion/SKILL.md](../../io-conversion/SKILL.md).

## `stat` fails or prints unexpected metadata

`stat` is a thin wrapper around `vaex.open`. A failure is usually an open/plugin
issue, not a separate metadata subsystem failure. If it succeeds but metadata
looks sparse, the dataset may not have descriptions, units, or UCDs populated.
For value checks, bounded samples, or lazy expression validation, route to
[../dataframe-core/SKILL.md](../../dataframe-core/SKILL.md) or
[../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md).

## Alias surprises

Symptoms:

- `vaex.open("name")` opens a different file than expected.
- `vaex alias remove name` raises because the alias is absent.
- `vaex alias list` reveals machine-specific paths.

Actions:

1. Inspect with `vaex alias list` only.
2. Ask before changing aliases; they are user-level state.
3. Prefer explicit local paths in automation unless a stable alias is part of
   the user's requested environment.
4. Do not publish alias targets from a user's machine.

If an alias should be changed temporarily for a script, avoid global mutation:
pass the explicit path or set process-local settings in Python and exit.

## Settings schema or diff command fails

Possible messages include missing `schema_json` or unsupported
`exclude_defaults` arguments. This can happen when Vaex is using its lightweight
settings implementation. It does not necessarily mean the configuration is
broken.

Actions:

```bash
vaex settings yaml
vaex settings json
python scripts/vaex_settings_probe.py --pretty
```

Use the probe's field/environment summary or `vaex settings md` as a fallback.
When reporting the issue, include the Vaex version and command that failed, but
redact path values.

## Environment variable does not seem to apply

Checklist:

1. Was the variable exported before importing Vaex or launching the `vaex`
   command?
2. Is the variable name a leaf field such as `VAEX_NUM_THREADS`,
   `VAEX_DISPLAY_MAX_COLUMNS`, or `VAEX_CACHE`?
3. Is a Vaex home YAML value explicitly overriding the same top-level field in
   this version?
4. Is the value type valid? Boolean parsing accepts `True`, `true`, `1`,
   `False`, `false`, and `0`; positive integer constraints apply to thread
   counts.
5. Are you reading raw settings output that contains dynamic defaults, such as
   CPU-derived thread counts?

Use a fresh process for each priority test. Do not alter the user's persistent
settings file to debug a temporary environment-variable question.

## Mutating settings commands were run accidentally

If `vaex settings save`, `set`, or `save-defaults` was run in the user's real
configuration:

1. Stop running further save commands.
2. Locate the Vaex home directory with a private `vaex settings json` or Python
   inspection, but do not paste the absolute path into public docs.
3. Ask the user whether to back up, inspect, edit, or remove the generated
   `main.yml`.
4. Prefer a manual, user-approved edit over automated deletion.

For future tests, isolate `VAEX_HOME` to a temporary directory and delete that
temporary directory after the probe.

## Developer-only and expensive commands

- `vaex settings docgen` rewrites a documentation file in the current source or
  working tree. Running it from an arbitrary project can fail or modify the
  wrong file.
- `vaex settings watch` launches docgen and waits for changes. It is not a
  diagnostic for users.
- `vaex benchmark` expects a dataset and expressions and can consume significant
  CPU/memory.
- `vaex test` starts a test runner whose coverage depends on optional packages,
  compiled extensions, plotting/server dependencies, and fixture availability.

Only run these commands after the user gives a concrete purpose, scope, runtime
budget, and allowed output locations.
