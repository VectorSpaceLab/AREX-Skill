# Vaex cross-cutting troubleshooting

Use this reference when the problem spans installation, importability, version skew, optional extras, source-build issues, settings, cache paths, or server startup behavior. For workflow-specific issues, route to the nearest sub-skill:

- DataFrame basics, column access, lazy evaluation: [../sub-skills/dataframe-core/SKILL.md](../sub-skills/dataframe-core/SKILL.md)
- File import/export/conversion and format plugins: [../sub-skills/io-conversion/SKILL.md](../sub-skills/io-conversion/SKILL.md)
- Expressions, aggregations, joins, and statistics: [../sub-skills/expressions-analytics/SKILL.md](../sub-skills/expressions-analytics/SKILL.md)
- ML pipelines and sklearn wrappers: [../sub-skills/ml-pipelines/SKILL.md](../sub-skills/ml-pipelines/SKILL.md)
- Plotting and Jupyter widgets: [../sub-skills/visualization-jupyter/SKILL.md](../sub-skills/visualization-jupyter/SKILL.md)
- `vaex server`, REST, WebSocket, and GraphQL: [../sub-skills/serving-remote/SKILL.md](../sub-skills/serving-remote/SKILL.md)
- Console commands, settings, aliases, and environment variables: [../sub-skills/cli-settings/SKILL.md](../sub-skills/cli-settings/SKILL.md)

## Fast triage

Run the bundled environment checker first, then the safe CLI probe if the console exists:

```bash
python scripts/check_vaex_environment.py --pretty
vaex --help
vaex settings yaml
python - <<'PY'
import vaex
print(getattr(vaex, '__version__', 'unknown'))
PY
```

If the console script is missing, try `python -m vaex --help` from the intended environment.

## Failure matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'vaex'` | Vaex is not installed in the active interpreter | Activate the intended environment or install a published Vaex distribution in that interpreter. |
| `vaex: command not found` | Console scripts are not on `PATH` or the environment is not active | Use `python -m vaex --help` or the environment's Python explicitly. |
| Top-level help prints `usage veax` | Typo in this Vaex line's help text | Ignore the typo; the console entry point is still `vaex`. |
| `vaex version` raises `AttributeError` for `__full_name__` | Version-specific CLI bug in the published package | Use `python -c 'import vaex; print(vaex.__version__)'` or the environment checker. |
| `vaex settings schema` or `vaex settings yaml-diff` fails | Lightweight settings backend does not implement the expected method | Use `vaex settings yaml/json/md` or [../sub-skills/cli-settings/scripts/vaex_settings_probe.py](../sub-skills/cli-settings/scripts/vaex_settings_probe.py). |
| `vaex settings save`, `set`, or `save-defaults` mutates unexpected files | These commands write to Vaex home YAML | Ask before using them; prefer environment variables or a temporary `VAEX_HOME` for experiments. |
| `vaex open --delete` removed files | The flag deletes failing inputs | Stop using it; always use `--dry-run` for validation unless deletion is explicitly intended. |
| `vaex convert` removed a failed output | Conversion cleanup deletes failed output by default unless `--no-delete` is passed | Re-run with `--no-delete` when debugging and keep the failed output path under review. |
| `vaex server` appears to hang or download data | It starts a long-running listener and may initialize example data when no datasets are supplied | Use the server sub-skill, bind to loopback, and prefer explicit dataset names plus a temporary `VAEX_HOME`. |
| `vaex.server.fastapi` import triggers example-data/cache behavior | The FastAPI module initializes server globals on import in some versions | Patch the example dataset in a temporary environment before import, or use the bundled server smoke script. |
| FastAPI `TestClient` complains about missing `httpx2` | The installed FastAPI/Starlette stack expects `httpx2` for client testing | Install `httpx2` in the private inspection environment before running route checks. |
| Plot smoke or notebook rendering fails headlessly | Matplotlib backend is interactive-only or missing | Use `Agg` for terminal checks and keep plotting in the visualization sub-skill. |
| ML wrappers fail to import | `vaex-ml`, `scikit-learn`, `numba`, or an optional estimator package is missing | Install only the packages needed for the requested ML workflow and retry. |
| File open fails even though Pandas can read it | A format/plugin mismatch or a Pandas-oriented layout | Route to the IO sub-skill for conversion/open diagnostics and plugin checks. |
| Source build or editable install fails | The checkout needs submodules, compiled extensions, and PCRE/build dependencies | Prefer a published wheel or conda-forge package; if source work is required, treat it as a source-build task, not a runtime usage bug. |

## Safe command checklist

Before running a command that can mutate user state, ask first:

- `vaex open --delete ...`
- `vaex alias add ...` / `vaex alias remove ...`
- `vaex settings save` / `set` / `save-defaults`
- `vaex settings docgen` / `watch`
- `vaex convert` without `--no-delete`
- `vaex server` on anything other than loopback for a private test
- `vaex benchmark` or broad `vaex test`

## Practical isolation pattern

When you need to inspect Vaex behavior without mutating the user profile, create a temporary home and explicit data/cache directories for that process only:

```bash
TMP_VAEX_HOME="$(mktemp -d)"
TMP_VAEX_DATA="$(mktemp -d)"
TMP_VAEX_CACHE="$(mktemp -d)"
VAEX_HOME="$TMP_VAEX_HOME" VAEX_DATA_PATH="$TMP_VAEX_DATA" VAEX_CACHE_PATH="$TMP_VAEX_CACHE" \
  python scripts/check_vaex_environment.py --pretty
rm -rf "$TMP_VAEX_HOME" "$TMP_VAEX_DATA" "$TMP_VAEX_CACHE"
```

Use a similar pattern for server and CLI experiments when example data, cache paths, or settings writes might otherwise land in the user's home directory.
