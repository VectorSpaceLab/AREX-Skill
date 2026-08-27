# Configuration And CLI Operating Guide

This guide is self-contained for Sacred 0.8.7 configuration and command-line work. Use it to design an experiment configuration, inspect what a run will see, and translate between Python API runs and command-line invocations.

## Configuration resolution model

For a run, Sacred builds the effective configuration in this practical order:

1. **Explicit updates** from `config_updates` or CLI `with key=value` are recorded first and treated as fixed values.
2. **Named configs** are evaluated in the order requested. They can set defaults for variants, but explicit updates have precedence.
3. **Normal configs** from config scopes, dictionaries, and config files are evaluated in declaration order.
4. **Config hooks** can return additional updates after the current ingredient or experiment config has been evaluated. Explicit updates still win over hook-provided values.
5. Sacred finalizes the seed and injects the final config into captured functions and commands.

Use `print_config` before a real run whenever you need to inspect this final result.

## Defining default configuration

### Config scopes: `@ex.config`

A config scope is a regular Python function decorated with `@ex.config` or `@ingredient.config`. Local variables assigned in the function body become config entries.

```python
from sacred import Experiment

ex = Experiment("demo")

@ex.config
def cfg():
    # inline comments are shown by print_config
    epochs = 10
    model = {"hidden": 128, "dropout": 0.1}
    if epochs > 5:
        schedule = "long"
```

Operational rules:

- Do not use `return` or `yield` in a config scope. Sacred extracts and executes the function body; `return`/`yield` raise syntax errors such as "No return statements allowed in ConfigScopes".
- Do not use `*args`, `**kwargs`, or default argument values in config scope functions.
- A config scope may declare parameters to read values already available from earlier config sources, fixed updates, or ingredient fallbacks. Declare only the values you actually need.
- Docstrings and nearby comments are captured and displayed by `print_config` as documentation.
- Prefer JSON-like values (`dict`, `list`, `str`, `int`, `float`, `bool`, `None`) for future storage compatibility. Tuples are normalized to lists for config storage.

### Config dictionaries: `add_config`

Use dictionaries or keyword arguments for explicit default config:

```python
ex.add_config({"batch_size": 32, "optimizer": {"name": "adam", "lr": 1e-3}})
ex.add_config(seed=42, debug=False)
```

Rules:

- Pass either one positional value or keyword arguments, not both.
- Passing no config raises an empty-config error.
- Later config sources can override or extend earlier dictionaries in declaration order.
- Nested dictionaries are merged when fixed updates target only a sub-key.

### Config files

`add_config("settings.json")` and `add_config("settings.pickle")` load files as dictionaries. YAML files (`.yaml`/`.yml`) require PyYAML to be installed in the current Python environment. The same file formats can also be used as named config updates from the CLI.

Keep config files small and explicit. If a YAML file fails to load, switch to JSON/pickle or install/verify PyYAML before relying on YAML behavior.

## Key restrictions

Sacred validates config keys for storage compatibility. By default, keys must not:

- contain a dot (`.`), because dots are used for nested path notation;
- contain an equals sign (`=`), because CLI updates split on `=`;
- start with `$`, because Mongo-compatible storage treats those specially;
- be reserved jsonpickle tags such as `py/object` or start with `json://`.

If a user needs a logical key with one of those characters, redesign the config schema, for example `{"optimizer": {"lr": 0.001}}` instead of a literal key `"optimizer.lr"`. Disabling these checks through global settings is possible but is not a safe default for a reusable skill.

## Named configs

Named configs are optional variants. Define them with `@ex.named_config` or `ex.add_named_config(...)`.

```python
@ex.config
def defaults():
    lr = 1e-3
    batch_size = 32
    augmentation = "none"

@ex.named_config
def fast_dev():
    batch_size = 4
    augmentation = "light"

ex.add_named_config("large_batch", {"batch_size": 256})
```

Run them from Python:

```python
run = ex.run(named_configs=["fast_dev"], config_updates={"lr": 5e-4})
```

Run them from CLI:

```bash
python train.py with fast_dev 'lr=5e-4'
```

Operational rules:

- Multiple named configs are allowed; order matters.
- Regular config updates have precedence over named configs.
- A config file path in the `with` list is treated as a named config file. If a named config and a file name collide, the file path wins.
- Named configs for ingredients are addressed with their dotted ingredient path, for example `data.fast_dev`.

## Config hooks

A config hook can add or rewrite config values after the current config has been evaluated:

```python
@ex.config_hook
def derive_values(config, command_name, logger):
    return {"run_label": f"{command_name}-{config['seed']}"}
```

Rules:

- Signature must be exactly `(config, command_name, logger)`.
- Return a dictionary of updates, or return nothing/`None` to leave config unchanged.
- Hooks receive a deep copy of the current config and cannot rely on mutating it in place.
- Explicit CLI/API updates are re-applied after hook output, so user-provided updates remain fixed.

## Programmatic updates

Use `Experiment.run(...)` for Python-side execution:

```python
run = ex.run(
    command_name="train",
    named_configs=["fast_dev"],
    config_updates={"optimizer": {"lr": 1e-4}, "seed": 123},
)
```

Dotted keys are converted to nested dictionaries internally, so `{"optimizer.lr": 1e-4}` and `{"optimizer": {"lr": 1e-4}}` target the same nested value. Prefer nested dictionaries in Python code for clarity and CLI dotted notation for shell commands.

## CLI updates with `with`

The command-line update syntax is:

```bash
python experiment.py [COMMAND] with UPDATE UPDATE ... [options]
```

Each update is either:

- `name=value`: a config assignment;
- `nested.name=value`: a nested config assignment;
- `name_without_equals`: a named config or config file.

Values are parsed with Python literal syntax when possible: numbers, booleans, `None`, strings with quotes, lists, and dictionaries. If parsing fails and strict parsing is off, the value is used as a raw string.

Examples:

```bash
python experiment.py print_config with 'epochs=3' 'model.hidden=64'
python experiment.py train with fast_dev 'optimizer.lr=1e-4' 'tags=["smoke", "cpu"]'
python experiment.py save_config with 'config_filename="resolved.json"'
```

Important shell rule: quote the whole update token whenever the value contains spaces, nested quotes, brackets, braces, `$`, or shell-sensitive characters.

## Inspecting suspicious changes

`print_config` displays the final configuration and marks:

- **modified** entries that changed from defaults;
- **added** entries that were not present in defaults;
- **typechanged** entries where the value type changed;
- **doc** entries from config-scope docstrings/comments.

Sacred warns for added or typechanged entries. Added entries that are not used by captured functions usually indicate a typo and can raise a config error unless `--force`/`-f` is used. Prefer fixing the default config instead of forcing past suspicious updates.
