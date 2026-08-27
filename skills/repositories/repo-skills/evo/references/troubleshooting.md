# Cross-cutting Troubleshooting

Use this page for issues that affect multiple evo workflows before you dive into the workflow-specific sub-skill references.

| Signal | Likely cause | Safe recovery |
| --- | --- | --- |
| `ModuleNotFoundError: evo` or import failures right after install | The package was not installed into the active Python, or the Python version is below 3.10. | Reinstall into the intended environment with `pip install -e .` or `pip install evo`, then rerun `python -I -c "import evo"`. |
| `python requires version >= 3.10` | The interpreter is too old for this release. | Switch to Python 3.10+ and reinstall the package. |
| `No broken requirements found` is missing or `pip check` fails | The environment has mismatched or incomplete dependencies. | Reinstall the package and its required dependencies in a fresh isolated environment. |
| `ImportError` for `PyQt6`, `contextily`, or `rerun` | You asked for an optional GUI/geo/Rerun route without the extra installed. | Install only the needed extra (`evo[gui]`, `evo[geo]`, `evo[rerun]`) or skip that optional route. |
| Plot windows do not open, or backend errors mention `Agg`, `TkAgg`, or `qtagg` | The current Matplotlib backend does not match the environment. | Use the package defaults, or set `plot_backend` with `evo_config` for the current environment. In headless sessions, prefer `Agg`. |
| `evo_config` cannot write `~/.evo/settings.json` | The user settings directory is missing or not writable. | Fix the permissions or work on a writable copy for experiments. |
| `IPython is not installed` from `evo_ipython` | The shell helper depends on IPython being on `PATH`. | Install IPython in the same environment and rerun `evo_ipython`. |
| `cat_log feature not available on Windows` | `evo cat_log` is intentionally disabled on Windows. | Read the logfile directly with platform-native tools after using `evo pkg --logfile`. |
| `Optional dependency rerun-sdk is not installed` | The Rerun route was requested without the extra. | Install `rerun-sdk` or drop the Rerun flag. |
| `contextily` token or provider errors | The selected map provider needs an API token or a provider string that is not a tile provider. | Set `map_tile_api_token` only when required and verify the provider name before retrying. |
| The built-in smoke helper fails to find the console scripts | The environment's PATH does not include the package entry points. | Run the helper from the target environment or use the installed console scripts directly. |

## Where to go next

- Metric-specific flag, sync, and result-zip issues: [`sub-skills/metrics/references/troubleshooting.md`](../sub-skills/metrics/references/troubleshooting.md)
- Trajectory-file, bag, and converter issues: [`sub-skills/trajectory-data/references/troubleshooting.md`](../sub-skills/trajectory-data/references/troubleshooting.md)
- Result-archive and table-export issues: [`sub-skills/result-analysis/references/troubleshooting.md`](../sub-skills/result-analysis/references/troubleshooting.md)
- Settings, package-info, and IPython issues: [`sub-skills/configuration/references/troubleshooting.md`](../sub-skills/configuration/references/troubleshooting.md)
- Python API, plotting, and optional visualization issues: [`sub-skills/python-api/references/troubleshooting.md`](../sub-skills/python-api/references/troubleshooting.md)
