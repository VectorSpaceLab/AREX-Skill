# Configuration And CLI Troubleshooting

Use this when a Sacred 0.8.7 config or command-line invocation does not behave as expected.

## Shell quoting changed my value type

Symptoms:

- `with a="2"` produces integer `2`, not string `"2"`.
- A string with spaces is split into several tokens.
- Lists or dictionaries are mangled by the shell.

Cause: the shell strips outer quotes before Sacred receives argv. Sacred then parses each `value` as a Python literal when possible.

Fixes:

```bash
# String value
python experiment.py with 'name="Bob"'

# List/dict values
python experiment.py with 'layers=[64, 32]' 'metadata={"split": "valid", "fold": 0}'

# Negative/scientific/binary numeric literals
python experiment.py with 'lr=-.3e-7' 'mask=0b111000'
```

When calling `run_commandline(argv=[...])` or `subprocess.run([...])`, pass each update as one argv element and do not add shell-only quoting unless you want quote characters to be parsed by Sacred.

## `print_config` shows added or typechanged entries

Symptoms:

- `WARNING - root - Added new config entry: "x"`.
- `WARNING - root - Changed type of config entry "x" from int to str`.
- A run fails with a suspicious added config key.

Meaning:

- **modified**: known default was changed.
- **added**: the key was not present in defaults.
- **typechanged**: the new value has a different type from the default.

Fix checklist:

1. Run `print_config` with the same `with` arguments.
2. If the key is a typo, fix the update path.
3. If the key is intentional, add it to the default config with a safe default.
4. If the type changed unintentionally, quote or unquote the value correctly. Example: use `'flag=True'` for bool, `'flag="True"'` for string.
5. Use `-f`/`--force` only for deliberate one-off experiments; it hides safety checks rather than fixing the schema.

## Dotted update created nested keys instead of a literal key

`with 'optimizer.lr=0.001'` means `{"optimizer": {"lr": 0.001}}`. It does not set a literal key named `optimizer.lr`.

Sacred config keys are intended to be storage-safe. By default, invalid keys include:

- keys containing `.`;
- keys containing `=`;
- string keys starting with `$`;
- reserved jsonpickle tags such as `py/object`, `py/tuple`, and keys starting with `json://`.

Fix by renaming the schema:

```python
# Good
ex.add_config({"optimizer": {"lr": 0.001}})

# Avoid
ex.add_config({"optimizer.lr": 0.001})
```

## `ConfigScope` fails with return/yield errors

Symptoms:

- `No return statements allowed in ConfigScopes`.
- `No yield statements allowed in ConfigScopes`.

Cause: Sacred extracts the body of a config-scope function and executes it as a block. A config scope communicates through local assignments, not a return value.

Fix:

```python
@ex.config
def cfg():
    # Good: assign locals
    width = 128
    model = {"width": width}

# Avoid returning model from cfg().
```

Also remove `*args`, `**kwargs`, and default argument values from config-scope functions. If a scope needs an earlier config value, declare it as a parameter with no default.

## Config scope cannot see a value

Symptoms:

- `KeyError: 'x' not in preset for ConfigScope`.
- `NameError` when reading a variable that looks like an earlier config value.

Fixes:

- Put dependent config scopes after the scopes/dicts that define the dependency.
- Declare the dependency as a config-scope argument: `def cfg2(x): ...`.
- Do not read arbitrary caller locals/globals as config inputs; make dependencies explicit config values.

## Nested config is read-only in a captured function

Symptoms:

- `The configuration is read-only in a captured function!`
- Mutating `_config`, a nested dict, or a list inside a captured function fails.

Cause: Sacred wraps dicts/lists in read-only containers for captured functions so untracked mutations cannot silently change the recorded configuration.

Fixes:

```python
@ex.capture
def transform(params):
    local_params = dict(params)  # copy before editing
    local_params["threshold"] = 0.7
    return local_params
```

Prefer returning a derived value or copying before mutation. Disabling read-only config globally is not recommended for reproducible runs.

## Unknown command or wrong command executed

Symptoms:

- `Error: Command "train" not found`.
- `with` updates are treated as command names or ignored.
- The main command runs when a custom command was intended.

Fix checklist:

1. Put the command name before `with`: `python experiment.py train with 'seed=1'`.
2. Verify the function is decorated with `@ex.command`, `@ingredient.command`, `@ex.main`, or `@ex.automain`.
3. For ingredient commands, use the dotted ingredient path, for example `data.prepare`.
4. Run `python experiment.py help` to list commands.
5. Run `python experiment.py help COMMAND` to inspect a command signature/docstring.
6. If no command is defined, add `@ex.main` or pass `command_name` to `ex.run(...)`.

## Named config not found

Symptoms:

- A `with variant` token fails as an unknown named config.
- An ingredient named config is not applied.

Fixes:

- Run `print_named_configs` to list valid names.
- Use dotted ingredient names for ingredient variants, such as `model.large`.
- Check ordering when multiple named configs set the same key.
- Remember that a file path in the `with` list is treated as a config file if it exists.

## YAML config files fail

Symptoms:

- `.yaml` or `.yml` config files fail to load.
- `save_config` to YAML fails.

Cause: YAML support requires PyYAML in the current Python environment.

Fixes:

- Use JSON for portable smoke tests: `config_filename="resolved.json"`.
- If YAML is required, install and verify PyYAML in the active environment before claiming YAML support.
- Keep YAML verification separate from base Sacred CLI verification unless the task explicitly requires YAML.

## Custom CLI option fails

Symptoms:

- Usage text does not include a custom flag.
- The option handler never runs.
- Flag creation raises a malformed flag error.

Fixes:

- Decorate a handler with `@cli_option("-z", "--tag")` or `@cli_option("-x", "--dry-run", is_flag=True)`.
- Pass the returned option object through `Experiment(..., additional_cli_options=[tag_option])`.
- Short flags must be one dash plus one word character, such as `-z`.
- Long flags must start with `--` and end with a word character, such as `--tag` or `--run-tag`.
- Remember non-flag options receive a string argument; convert to `int`, `float`, or `bool` inside the handler if needed.

## Observer flags fail from CLI

The CLI flags `-m/--mongo_db`, `-s/--sql`, and `-t/--tiny_db` require optional packages and, for Mongo/SQL, external services or valid local database endpoints. Do not treat failures from these flags as base CLI failures unless the task explicitly requires that optional observer.

Safe local checks can use:

```bash
python experiment.py main -u -C no with 'seed=1'
python experiment.py print_config with 'seed=1'
```

Use `-F/--file_storage` for local file observer workflows only when storage behavior is in scope; route directory-layout questions to `observers-and-logging`.

## Save config wrote an unexpected format or location

`save_config` writes `config.json` by default in the current working directory. Override the filename through config:

```bash
python experiment.py save_config with 'config_filename="resolved.json"'
```

The extension selects the writer. Use `.json` for a dependency-light output. YAML output requires PyYAML.
