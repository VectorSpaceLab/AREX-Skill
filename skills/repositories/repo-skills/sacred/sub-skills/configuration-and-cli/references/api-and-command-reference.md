# API And Command Reference

This reference is for Sacred 0.8.7. It focuses on configuration and command-line surfaces. For run objects, observers, metrics, artifacts, resources, capture modes, and reproducibility internals, route to the sibling sub-skills named in `SKILL.md`.

## Relevant constructor and run signatures

| Object | Sacred 0.8.7 signature | Use here |
|---|---|---|
| `Experiment.__init__` | `Experiment(name=None, ingredients=(), interactive=False, base_dir=None, additional_host_info=None, additional_cli_options=None, save_git_info=True)` | Create the experiment, attach ingredients, and pass custom CLI options. |
| `Experiment.run` | `Experiment.run(command_name=None, config_updates=None, named_configs=(), info=None, meta_info=None, options=None)` | Programmatic equivalent of CLI command routing plus `with` updates. |
| `Experiment.run_commandline` | `Experiment.run_commandline(argv=None)` | Parse CLI argv. Use with `if __name__ == "__main__": ex.run_commandline()`. |
| `Ingredient.__init__` | `Ingredient(path, ingredients=(), interactive=False, _caller_globals=None, base_dir=None, save_git_info=True)` | Create reusable config/command namespaces. |
| `Ingredient.capture` | `Ingredient.capture(function=None, prefix=None)` | Captured functions receive config values; detailed capture semantics route elsewhere. |
| `Ingredient.command` | `Ingredient.command(function=None, prefix=None, unobserved=False)` | Add custom commands and ingredient-scoped command routes. |
| `Ingredient.add_config` | `Ingredient.add_config(cfg_or_file=None, **kw_conf)` | Add default config from dict, file, or keyword config. `Experiment` inherits this. |

Additional installed signatures that often appear near this surface but route elsewhere: `Experiment.add_artifact(filename, name=None, metadata=None, content_type=None)`, `Experiment.log_scalar(name, value, step=None)`, `Run.add_artifact(filename, name=None, metadata=None, content_type=None)`, `Run.log_scalar(metric_name, value, step=None)`, and `FileStorageObserver.__init__(basedir, resource_dir=None, source_dir=None, template=None, priority=20, copy_artifacts=True, copy_sources=True)`.

## Config API quick table

| Task | API | Notes |
|---|---|---|
| Add config scope | `@ex.config` / `@ingredient.config` | Locals become entries; no `return`/`yield`; comments appear in `print_config`. |
| Add config dict | `ex.add_config({"a": 1})` | Use JSON-like values and valid keys. |
| Add config kwargs | `ex.add_config(a=1, b=True)` | Cannot combine with a positional dict/file. |
| Add config file | `ex.add_config("conf.json")` | `.json` and `.pickle` work with base dependencies; `.yaml`/`.yml` require PyYAML. |
| Add named scope | `@ex.named_config` | Function name becomes named config id. |
| Add named dict/file | `ex.add_named_config("name", {...})` or `ex.add_named_config("name", "file.json")` | Duplicate names raise an error. |
| Add config hook | `@ex.config_hook` with `(config, command_name, logger)` | Return a dict of derived updates. |
| Run with updates | `ex.run(config_updates={"a": 2})` | Nested dicts and dotted keys target nested paths. |
| Run named config | `ex.run(named_configs=["variant"])` | Order matters. |
| Parse explicit argv | `ex.run_commandline(["prog.py", "train", "with", "a=2"])` | The first argv element is the program name. |

## CLI grammar

Canonical pattern:

```bash
python experiment.py [COMMAND] with UPDATE UPDATE ... [options]
python experiment.py help [COMMAND]
python experiment.py print_config with UPDATE ...
```

Notes:

- `COMMAND` must be the first non-option command token. If omitted, Sacred runs the default command created with `@ex.main` or `@ex.automain`.
- `with` starts the config/named-config update list.
- `name=value` is an assignment; `name` without `=` is a named config or config file.
- Dotted assignments create/target nested dictionaries: `optimizer.lr=0.001` means `{"optimizer": {"lr": 0.001}}`.
- List element updates are not supported; replace the whole list, for example `'layers=[64, 32]'`.
- Values are parsed as Python literals when possible; raw strings are used as fallback when strict command-line parsing is disabled.

## Built-in commands

| Command | Purpose | Typical use |
|---|---|---|
| `print_config` | Print the effective config and mark modified/added/typechanged/doc entries. | Validate `with` updates and named configs before running training. |
| `print_dependencies` | Print discovered dependencies, source files, and version-control state. | Reproducibility inspection; route deeper dependency/source questions to `reproducibility-and-capture`. |
| `print_named_configs` | List available named configs, including ingredient-prefixed names and short docstrings. | Discover valid `with variant` tokens. |
| `save_config` | Save the effective config; defaults to `config.json`. | Materialize a resolved config with `with 'config_filename="resolved.json"'`. |
| `help` | Print usage, commands, options, or command-specific signature/docstring. | Diagnose command routing and custom command signatures. |

Examples:

```bash
python experiment.py print_config with fast_dev 'seed=123' 'optimizer.lr=1e-4'
python experiment.py print_named_configs
python experiment.py help train
python experiment.py save_config with 'config_filename="resolved.json"'
```

## Command routing

Custom commands are regular captured functions:

```python
@ex.command
def evaluate(split, threshold=0.5):
    ...
```

Run from CLI:

```bash
python experiment.py evaluate with 'split="valid"' 'threshold=0.7'
```

Run from Python:

```python
ex.run(command_name="evaluate", config_updates={"split": "valid", "threshold": 0.7})
```

Rules:

- The main function registered by `@ex.main` or `@ex.automain` is also a command and can be named explicitly.
- Ingredient commands use dotted paths, such as `data.prepare`, when the ingredient path is `data` and the command name is `prepare`.
- `@ex.command(unobserved=True)` creates helper commands that should not trigger observers.
- `help COMMAND` shows a command signature and docstring.
- Unknown command errors usually mean the command token is in the wrong position, the decorator is missing, the ingredient prefix is wrong, or there is no default command.

## CLI flags

| Flag | Long option | Effect | Dependency/caveat |
|---|---|---|---|
| `-h` | `--help` | Print usage. | Equivalent to `help`. |
| `-l LEVEL` | `--loglevel=LEVEL` | Set logging level by name or number. | Useful to suppress `INFO` logs during probes. |
| `-F BASEDIR` | `--file_storage=BASEDIR` | Add a local file-storage observer. | Storage layout details route to `observers-and-logging`. |
| `-m DB` | `--mongo_db=DB` | Add MongoDB observer. | Requires `pymongo` and a reachable MongoDB service. |
| `-t BASEDIR` | `--tiny_db=BASEDIR` | Add TinyDB observer. | Requires `tinydb`, `tinydb-serialization`, and `hashfs`. |
| `-s DB_URL` | `--sql=DB_URL` | Add SQL observer. | Requires SQLAlchemy and a valid database URL. |
| `-u` | `--unobserved` | Ignore observers and silence missing-observer warnings. | Useful for smoke tests. |
| `-q` | `--queue` | Queue run without starting it. | Requires an observer that supports queued runs. |
| `-p` | `--print-config` | Print config before running the selected command. | Like `print_config` plus real command execution. |
| `-n NAME` | `--name=NAME` | Set run/experiment name for this run. | Affects observer metadata/loggers. |
| `-i ID` | `--id=ID` | Set run id. | Useful with observers that accept explicit ids. |
| `-C MODE` | `--capture=MODE` | Set stdout/stderr capture mode: `no`, `sys`, or `fd`. | Capture-mode internals route to `reproducibility-and-capture`. |
| `-d` | `--debug` | Do not filter stack traces; also suppresses missing-observer warnings. | Use for debugging, not routine production runs. |
| `-D` | `--pdb` | Enter post-mortem `pdb` on failure. | Interactive/debug only. |
| `-f` | `--force` | Disable warnings/errors for suspicious config changes. | Prefer fixing config; use only when intentional. |
| `-c COMMENT` | `--comment=COMMENT` | Add a run comment. | Stored in run metadata. |
| `-b SECONDS` | `--beat-interval=SECONDS` | Set heartbeat interval. | Observer heartbeat semantics route elsewhere. |
| `-P PRIORITY` | `--priority=PRIORITY` | Set numeric queued-run priority. | Mostly for queued observer workflows. |
| `-e` | `--enforce_clean` | Fail if discovered VCS repositories are dirty. | Requires GitPython and route details to reproducibility. |

Optional cloud/chat observer flags may exist in an environment with the relevant optional packages, credentials, and services. Do not claim those are available unless a safe local probe verifies the imports and the task has authorized service use.

## Custom CLI options

Use `sacred.cli_option` for custom flags:

```python
from sacred import Experiment, cli_option

@cli_option("-z", "--tag")
def tag_option(args, run):
    """Attach a tag to run info."""
    run.info["tag"] = args

@cli_option("-x", "--dry-run", is_flag=True)
def dry_run_option(args, run):
    """Mark this run as dry-run."""
    run.info["dry_run"] = bool(args)

ex = Experiment("demo", additional_cli_options=[tag_option, dry_run_option])
```

Rules:

- Short flags must look like `-z`; long flags must look like `--tag` or `--my-flag`.
- If `is_flag=True`, the handler receives `True` when present. Otherwise it receives a string argument.
- The handler is called after the `Run` object is created and before it starts.
- Modify run metadata/options in the handler; do not start services or perform destructive work from option handlers.

CLI use:

```bash
python experiment.py train --tag=smoke --dry-run with 'epochs=1'
```
