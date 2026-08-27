# Configuration and widget troubleshooting

## First checks

```python
import lux
import pandas as pd

print(type(pd.DataFrame({"x": [1, 2, 3, 4, 5]})))
print(lux.debug_info(return_string=True))
```

Expected signals:

- After `import lux`, new Pandas dataframes should be instances of Lux's dataframe subclass.
- `lux.debug_info(return_string=True)` should return a string containing `Package Versions`, `python`, `lux`, `pandas`, `luxwidget`, `matplotlib`, `altair`, and `Widget Setup`.
- If Lux was imported after the dataframe was created, recreate the dataframe after `import lux`.

## Widget does not display

Use `lux.debug_info()` inside the same notebook environment where display fails. Interpret the widget setup section:

- `IPython shell not available` means the code is not running in a notebook-like interface. Lux recommendations can still be inspected programmatically, but the interactive widget requires Jupyter Notebook, JupyterLab, JupyterHub, VS Code notebooks, or a compatible frontend.
- A JupyterLab warning that `luxwidget` is not enabled can usually be repaired from the terminal used to launch that Lab server:

  ```bash
  jupyter labextension install @jupyter-widgets/jupyterlab-manager
  jupyter labextension install luxwidget
  ```

- A classic Notebook warning that `luxwidget` is not enabled can usually be repaired with:

  ```bash
  jupyter nbextension install --py luxwidget
  jupyter nbextension enable --py luxwidget
  ```

  If permission errors occur, add `--user` to the install/enable commands.

- If `LuxWidget(...)` prints but no UI appears, check that notebook extensions list an enabled `luxWidget/extension` and try a supported browser. Re-run the cell or restart the kernel if the frontend says widget state could not be found.
- If `ModuleNotFoundError: No module named 'luxwidget'` appears, reinstall matching Lux packages in the environment used by the notebook:

  ```bash
  pip uninstall -y lux-api lux-widget jupyterlab_widgets
  pip install lux-api
  ```

  Then enable the appropriate notebook or lab extension again.

## Config changes do not affect existing recommendations

Lux caches generated recommendations. Set configuration before first display when possible. For an already displayed dataframe:

```python
lux.config.default_display = "lux"
lux.config.plotting_backend = "vegalite"
lux.config.topk = 6
df.expire_recs()
df
```

If several dataframes are open, call `expire_recs()` on each one. Registering or removing a custom action marks Lux's action manager as changed, but explicit `expire_recs()` is still the safest way to force a visible refresh.

## Invalid configuration values

Common symptoms and fixes:

- `Unsupported display type`: use only `lux.config.default_display = "lux"` or `"pandas"`.
- `Unsupported plotting backend`: use only `"vegalite"`, `"altair"`, or `"matplotlib"`.
- `Parameter to lux.config.sort must be one of...`: use `"descending"`, `"ascending"`, or `"none"`.
- `Parameter to lux.config.topk must be an integer or a boolean`: use an integer or `False`.
- Sampling assertion errors: maintain `sampling_start <= sampling_cap` at every assignment.
- Silent fallback to a Pandas table: temporarily set `lux.config.pandas_fallback = False` to expose the underlying exception.
- Silent loss of interestingness scores: temporarily set `lux.config.interestingness_fallback = False` to expose scoring exceptions.

Many config setters warn and preserve the previous value. Some setters lowercase inputs before validation, so non-string values for string settings can raise instead of warn.

## Custom action does not appear

Check these in order:

1. The dataframe has at least five rows and is not empty.
2. The action was registered under the expected name: `ACTION_NAME in lux.config.actions`.
3. The validator returns true for that dataframe: `lux.config.actions[ACTION_NAME].display_condition(df)`.
4. The action function returns a dictionary with `"action"`, `"description"`, and a non-empty `"collection"`.
5. The returned `"action"` string is the key you are looking for in `df.recommendation`.
6. The dataframe recommendations were refreshed: `df.expire_recs(); df.maintain_recs()` or redisplay the dataframe in a notebook.

Invalid custom action failures are explicit:

- Non-callable action: `ValueError("Action must be a callable")`.
- Non-callable display condition: `ValueError("Display condition must be a callable")`.
- Removing an unknown action: `ValueError("Option '<name>' has not been registered")`.

## Export and SQL boundaries

- If a user wants to export one selected chart or inspect `df.exported`, route to `visualization-export`.
- If a user wants to call `set_SQL_connection`, construct `LuxSQLTable`, or troubleshoot PostgreSQL/service errors, route to `sql-backend`.
- This sub-skill may switch back to the local dataframe executor with `lux.config.set_executor_type("Pandas")`.
