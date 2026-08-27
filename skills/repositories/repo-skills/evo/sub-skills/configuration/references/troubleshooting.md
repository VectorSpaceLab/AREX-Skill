# Troubleshooting

| Signal | Meaning | Safe recovery |
|---|---|---|
| `No permission to modify ...` from `evo_config set` or `reset` | The selected settings file is read-only or not writable by the current user. | Work on a writable copy with `evo_config set -c <copy> ...`. For `reset`, fix the package settings file permissions first because `reset` has no `-c` target. |
| `IPython is not installed` from `evo_ipython` | Neither `ipython3` nor `ipython` is available on `PATH`. | Install IPython in the same environment that provides evo, then rerun `evo_ipython`. |
| `IPython profile for evo is not installed` | First launch could not locate the `evo` IPython profile. | This is expected on first run. Let `evo_ipython` create the profile and copy its config, then continue. |
| `no logfile found - run: evo_config set global_logfile_enabled` | The global logfile path exists as a setting, but no logfile has been created yet. | Enable logging with `evo_config set global_logfile_enabled true`, rerun a command that logs, then inspect with `evo cat_log`. |
| `logfile disabled` from `evo cat_log` | You tried to pipe or write a message while `global_logfile_enabled` is false. | Enable the setting or use `evo cat_log` only in read mode after a logfile exists. |
| `cat_log feature not available on Windows` | `evo cat_log` is explicitly disabled on Windows. | Use `evo pkg --logfile` to locate the file and inspect it directly with platform-native tools. |
| A `set` or `reset` key appears to do nothing | The key may be misspelled, absent from the target JSON, or not part of the current settings template. CLI edits only update recognized/existing keys, and Python `SETTINGS.<unknown>` raises `SettingsException`. | Confirm the key in `references/settings.md`, run `evo_config show --brief --no_color`, and reapply the edit with options before positional key/value tokens. |
| `Invalid JSON` or merge-file parsing fails | The overlay file is not valid JSON, or the merge target is not writable. | Fix the JSON syntax, then rerun `evo_config set -m <overlay>` or work on a writable copy. |
| `generate -o` prompts for overwrite or fails in a noninteractive shell | The output file already exists and the command is waiting for confirmation. | Pick a new path first, or run the command in an interactive shell where overwrite confirmation is possible. |
| A boolean changed unexpectedly | Passing a boolean key with no value toggles it. | Use explicit values such as `evo_config set plot_usetex false` when you do not want toggle behavior. |
| Plot backend changes do not affect an IPython/Jupyter session | `evo.tools.plot.apply_settings()` intentionally does not override the interactive shell backend. | Set the backend before importing evo plotting helpers, or use the shell's Matplotlib backend controls in that session. |

## Read-only fallback checklist
1. Inspect first: `evo_config show --brief --no_color`.
2. If a write fails, copy `~/.evo/settings.json` to a writable path and use `-c` on that copy.
3. Compare with defaults: `evo_config show --diff --no_color`.
4. Keep all `evo_config` options before trailing setting names or key/value tokens.
