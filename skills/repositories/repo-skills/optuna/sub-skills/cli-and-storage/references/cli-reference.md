# Optuna CLI Reference

Optuna exposes a console script named `optuna` that dispatches to `optuna.cli:main`. Do not use `python -m optuna`; the package is not a module entry point.

## Global CLI Options

Global options can appear before or after the subcommand because Optuna preprocesses the command name before parsing:

- `--storage STORAGE`: storage URL or journal file path. Also read from `OPTUNA_STORAGE` when omitted.
- `--storage-class STORAGE_CLASS`: storage class hint. Accepted current choices are `RDBStorage`, `JournalFileBackend`, and `JournalRedisBackend`; deprecated accepted aliases include `JournalFileStorage` and `JournalRedisStorage`.
- `-v` / `--verbose`: increase logging verbosity; repeatable.
- `-q` / `--quiet`: suppress normal output except warnings/errors.
- `--log-file LOG_FILE`: write logs to a file.
- `--debug`: show tracebacks on errors.
- `--version`: print the Optuna version.

Storage inference rules from `optuna.cli`:

- A URL beginning with `redis` is treated as `JournalStorage(JournalRedisBackend(url))`.
- An existing file path is treated as `JournalStorage(JournalFileBackend(path))`.
- Otherwise Optuna attempts `RDBStorage(storage_url)`.
- If inference fails, pass `--storage-class` explicitly.

## Command Catalog

| Command | Purpose | Key options |
| --- | --- | --- |
| `create-study` | Create a study and print its name. | `--study-name`, `--direction {minimize,maximize}`, `--directions ...`, `--skip-if-exists` |
| `delete-study` | Delete a named study. | `--study-name` |
| `study set-user-attr` | Set a study-level user attribute. | `--study-name`, `--key`, `--value` |
| `study-names` | Print all study names in storage. | `--format {value,json,table,yaml}` |
| `studies` | List study summaries. | `--format`, `--flatten` |
| `trials` | List trials for one study. | required `--study-name`, `--format`, `--flatten` |
| `best-trial` | Show the best trial for a single-objective study. | required `--study-name`, `--format`, `--flatten` |
| `best-trials` | Show Pareto-front trials for a multi-objective study. | required `--study-name`, `--format`, `--flatten` |
| `storage upgrade` | Upgrade an RDB storage schema to the installed Optuna head revision. | `--storage` or `OPTUNA_STORAGE` |
| `ask` | Create a trial and emit suggested parameters. | `--study-name`, `--sampler`, `--sampler-kwargs`, `--search-space`, `--format`, `--flatten` |
| `tell` | Finish a trial created by `ask`. | `--study-name`, `--trial-number`, `--values`, `--state {complete,pruned,fail}`, `--skip-if-finished` |

## Local SQLite Ask/Tell Flow

Use this pattern when an external system, shell script, lab workflow, or manual experiment computes objective values outside Python.

```bash
storage="sqlite:///optuna-example.db"
study="cli-demo"

optuna create-study --storage "$storage" --study-name "$study" --direction minimize --skip-if-exists

search_space='{"x":{"name":"FloatDistribution","attributes":{"low":-10.0,"high":10.0,"step":null,"log":false}}}'
ask_json=$(optuna ask --storage "$storage" --study-name "$study" --sampler TPESampler --sampler-kwargs '{"seed": 0}' --search-space "$search_space" --format json)
trial_number=$(python -c 'import json,sys; print(json.load(sys.stdin)["number"])' <<< "$ask_json")

# Replace this toy value with the measured objective value from the external system.
optuna tell --storage "$storage" --study-name "$study" --trial-number "$trial_number" --values 0.25 --state complete
optuna trials --storage "$storage" --study-name "$study" --format table --flatten
```

Search-space values are JSON objects produced by Optuna distributions. For a float parameter, the CLI expects the same structure returned by `optuna.distributions.distribution_to_json(optuna.distributions.FloatDistribution(...))`.

## Multi-Objective CLI Notes

- Create multi-objective studies with `--directions`, for example `--directions minimize maximize`.
- Complete trials by passing one value per direction to `tell --values`, for example `--values 0.3 5.0 --state complete`.
- Use `best-trials` instead of `best-trial` for Pareto-front results.

## `OPTUNA_STORAGE`

When `--storage` is omitted, CLI commands read `OPTUNA_STORAGE`. This is useful for a shell session where every command targets the same backend:

```bash
export OPTUNA_STORAGE="sqlite:///optuna-session.db"
optuna create-study --study-name session-demo --direction minimize --skip-if-exists
optuna studies --format table
```

The environment-variable interface is marked experimental by Optuna and can emit an `ExperimentalWarning`.

## Journal File CLI Flow

A journal log file is not a SQLAlchemy URL. Pass a file path plus a storage-class hint:

```bash
journal="optuna-journal.log"
study="journal-cli-demo"
: > "$journal"
optuna create-study --storage "$journal" --storage-class JournalFileBackend --study-name "$study" --direction minimize --skip-if-exists
optuna studies --storage "$journal" --storage-class JournalFileBackend --format table
```

If the file already exists, Optuna can infer `JournalFileBackend` from the path, but the explicit hint makes scripts robust.

## Output Formats

Use `--format json` or `--format yaml` when another program will parse output. Use `--flatten` to flatten nested columns such as `params_x` and `user_attrs_owner` in `trials`, `studies`, `best-trial`, and `best-trials` output.

## CLI Behavior Worth Remembering

- `create-study` prints the study name. If no name is supplied, it returns a generated `no-name-...` identifier.
- `create-study --skip-if-exists` maps to `load_if_exists=True`-style behavior and avoids duplicate-name failures.
- `ask` no longer creates a study implicitly; create the study first.
- `ask --sampler-kwargs` requires `--sampler`.
- `tell --skip-if-finished` avoids failing when a completed/pruned/failed trial is reported again.
- `storage upgrade` is for RDB storage. Journal log files do not use the RDB schema migration path.
