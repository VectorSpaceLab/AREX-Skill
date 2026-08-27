# Integration Landscape

## When to read

Read this for a package-level view of optional integrations and how they relate
to the core report workflow.

## Optional dependency matrix

| Surface | Package / runtime | Notes |
| --- | --- | --- |
| Notebook widgets | `notebook` extra + `ipywidgets` | Needed for widget UI; HTML iframe is the safer fallback. |
| Spark profiling | `spark` extra + PySpark + Java | The package uses `[spark]` in metadata; some docs still mention `[pyspark]`. |
| Unicode naming | `unicode` extra | Base package falls back to Python `unicodedata` names when the extra is absent. |
| Great Expectations | external `great_expectations` | Current docs mark the integration as unsupported in modern versions. |

## Migration and compatibility notes

- `data_profiling` is the current import; `ydata_profiling` remains as a
  deprecated compatibility import.
- `data_profiling` and `pandas_profiling` are both installed as CLI commands;
  `data_profiling` is preferred.
- Some docs and examples still use older names such as `[pyspark]` or old import
  names. Verify against `pyproject.toml` and the current import surface before
  copying an install command.

## Streaming and app embedding

The package can be used in workflows where the report HTML is embedded into
other systems:

- Bytewax stream snapshots can profile windowed pandas DataFrames.
- Dash, Streamlit, and Panel can render report HTML inline or from assets.
- IDE external tools can call the installed CLI to profile the file currently
  open in an editor.

These patterns are best used after the core report workflow and output behavior
are already understood.

## Relationship to other sub-skills

- For Spark command-line readiness and limitations, see
  [spark-backend.md](spark-backend.md).
- For notebook widgets and Unicode extras, see
  [optional-dependencies.md](optional-dependencies.md).
- For troubleshooting, see [troubleshooting.md](troubleshooting.md).
