# CLI reference

## `evo_config`

Note: the `show`, `set`, and `reset` subcommands use a trailing `params...` list. Keep optional flags before those trailing keys so they are not consumed by the remainder parser.

### `show`
Flags:
- `-c` / `--config PATH` — read a JSON config file instead of `~/.evo/settings.json`
- `--brief` — print JSON only
- `--diff` — show a unified diff against the default settings
- `--no_color` — disable colored output
- trailing `params...` — limit output to named settings keys

Behavior:
- With no `-c` and no `--brief`, `show` prints parameter docs, the current config path, and then JSON.
- With `--diff`, it compares the selected config file against the package defaults.
- `show --brief --no_color` is the canonical machine-readable inspection command.

### `set`
Flags:
- `-c` / `--config PATH` — target config file to edit; default is `~/.evo/settings.json`
- `-m` / `--merge PATH` — merge another JSON config into the target after explicit edits
- `--soft` — when merging, keep existing keys and only add missing ones
- `--no_color` — disable colored diff output
- trailing `params...` — key/value edits in settings-key order

Behavior:
- Mutates the selected file in place.
- Booleans toggle when the key is given with no value; explicit `true` and `false` also work.
- Numeric strings are parsed as numbers.
- List-valued settings accept multiple tokens; `[]` or `none` clears a list.
- `plot_seaborn_palette` accepts either a palette name or an explicit color list.
- Merging is shallow: matching top-level keys are replaced or preserved, depending on `--soft`.

### `generate`
Flags:
- `-o` / `--out PATH` — write the generated JSON to a file
- `--no_color` — disable colored JSON output

Behavior:
- Converts the raw CLI tokens after `generate` into JSON keys and values.
- Long `--options` are preferred; combined short flags like `-vp` are discouraged.
- Without `-o`, the command prints JSON and saves nothing.
- With `-o`, overwrite is confirmed interactively.

### `reset`
Flags:
- `-y` — skip the confirmation prompt
- `--no_color` — disable colored output
- trailing `params...` — reset only those settings keys

Behavior:
- Resets the package settings file back to defaults.
- Partial reset only touches the named keys.
- No `-c` override exists for `reset`.

## `evo pkg`
Flags:
- `--info` — print usage plus the package description and command overview
- `--version` — print the evo version
- `--pyversion` — print the Python version
- `--license` — print the package license text
- `--location` — print the installed package path
- `--logfile` — print the logfile path
- `--open_log` — print the logfile path and open it
- `--clear_log` — prompt and truncate the logfile

Behavior:
- `--logfile` and `--open_log` report `no logfile found - run: evo_config set global_logfile_enabled` when the logfile is missing.
- `--clear_log` asks `clear logfile? (y/n)` and truncates the file on confirmation.

## `evo cat_log`
Flags:
- `-l` / `--loglevel {error,warning,info,debug}`
- `-m` / `--message TEXT`
- `-s` / `--source TEXT`
- `--clear_log`

Behavior:
- No stdin and no `--message`: print the logfile to stdout if it exists.
- Stdin or `--message`: write a log message to the global logfile, but only if `global_logfile_enabled` is true.
- `--source` rewrites the source label in the file log format.
- `--clear_log` truncates after the read/write action.
- Not available on Windows.

## `evo_ipython`
Flags:
- none of its own; unknown args are forwarded to IPython.

Behavior:
- Tries `ipython3`, then `ipython`.
- If the `evo` profile is missing, it creates it and copies `evo/ipython_config.py` into the profile directory.
- Launches `python -m IPython --profile evo`.
- The profile preloads `evo.core` modules (`lie_algebra`, `metrics`, `result`, `sync`, `trajectory`), `evo.tools` modules (`file_interface`, `pandas_bridge`, `plot`, `settings`), high-level `ape` and `rpe`, plus NumPy, Matplotlib, Seaborn, and pandas.
