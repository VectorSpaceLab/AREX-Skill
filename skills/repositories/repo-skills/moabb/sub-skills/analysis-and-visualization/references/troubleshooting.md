# Troubleshooting analysis and visualization

Use the symptom/check/recovery sequence below. Preserve the observed metric,
row count, and exception in the report rather than masking a data problem.

| Symptom | Likely cause | Check | Recovery |
|---|---|---|---|
| `KeyError` for `dataset`, `pipeline`, `subject`, `session`, or `score` | Input is not a MOABB result DataFrame or columns were renamed | Print `df.columns`, compare with [data formats](data-formats.md), and confirm `Results.to_dataframe()` was called | Restore canonical names or explicitly adapt a copy; do not pass an evaluation object to plotting functions |
| `chance_by_chance` fails or returns nonsense | Missing/NaN `samples_test`/`n_classes`, inconsistent values within a dataset, or a non-count score | Group by dataset and inspect `nunique`, nulls, metric/scoring property, and score range | Use explicit metric-specific chance; only calculate adjusted binomial levels for valid independent count/proportion scores |
| A multiclass plot shows 50% chance | Plot defaulted to 0.5 or caller supplied binary chance | Inspect `n_classes`, `chance_level`, and plotted annotation | Pass `chance_by_chance(df)` or an explicit per-dataset mapping; label metric and class count |
| A binary ROC-AUC plot shows an adjusted binomial threshold | `chance_by_chance` was applied without checking metric semantics | Inspect scoring metric and `samples_test` meaning | Keep 0.5 for ROC-AUC and remove adjusted threshold; use a suitable AUC test outside this route if needed |
| `compute_dataset_statistics` has NaN p-values/effects or too few rows | Incomplete pipeline pairs, duplicate units, one subject, or constant differences | Check duplicates and pivot completeness after `collapse_session_scores`; inspect `nsub` and finite `score` | Filter/aggregate with a declared rule, select complete pairs, or report that the comparison is underpowered; never impute silently |
| `summary_plot` labels collide or matrix shape is wrong | Pipeline names shorten to the same prefix, or `P`/`T` indices differ | Compare `P.index`, `P.columns`, `T.index`, `T.columns`, and simplified names | Call with `simplify=False` or preserve unique names; align matrices before plotting |
| `paired_plot` raises missing algorithm/NaN errors | Pipeline label absent or one pipeline lacks a subject/dataset pair | Inspect `df.pipeline.unique()` and paired pivot counts | Use exact labels and a complete paired subset; route an unpaired question to a different method |
| `ValueError: Invalid plot orientation selected` | Orientation is not `vertical`/`v`/`horizontal`/`h` | Print the value passed | Correct the option; preserve the default if no orientation choice is needed |
| Plot has no chance line | `chance_level=None` (the default) | Inspect call arguments and figure annotations | Pass scalar, mapping, or `"auto"`; remember `None` uses an internal 0.5 fallback but does not draw a line |
| Plot import or save fails in CI/SSH | Interactive Matplotlib backend or no display | Check `MPLBACKEND` and import order | Set `MPLBACKEND=Agg` before importing `moabb.analysis.plotting`; save to a writable path and close figures |
| `analyze` raises `Given directory does not exist` | `out_path` is missing or not a string | Check `isinstance(out_path, str)` and `os.path.isdir(out_path)` | Create/choose the parent directory first; the function creates `out_path/name`, not `out_path` |
| Report contains stale or mixed rows | Reused report name or DataFrame mutated/filtered unexpectedly | Compare `data.csv` with a saved input hash/row count; inspect `info.txt` and `name` | Use a fresh name, pass a copied filtered DataFrame, and retain a manifest outside the skill |
| `codecarbon_plot` errors or summary is `None` | Optional CodeCarbon was not installed or results contain no emissions | Check `carbon_emission` column and import availability | Skip emissions views and state unavailable; do not turn missing emissions into zero |
| Neural signature import is present but generation raises Plotly error | Plotly is optional and guarded at call time | `importlib.util.find_spec("plotly")`; read the exception | Install the project interactive extra if approved, or skip interactive HTML and use core Matplotlib/timeline APIs |
| Timeline title says approximate or phases are generic | Dataset metadata lacks protocol timing or has inconsistent fields | Inspect `StimulusTimeline.is_approximate`, `notes`, `paradigm`, and metadata availability | Keep the approximate label; do not invent timing. Use a dataset-specific metadata route if exact protocol is required |
| `plot_class_balance` or `plot_session_structure` returns `None` | Missing event IDs, trial counts, or session count | Inspect `dataset.event_id`, metadata, and `dataset.n_sessions` | Treat `None` as an honest unavailable chart; use a richer metadata fixture or omit the chart |
| Timeline SVG is empty/invalid | Figure was not rendered before closing, or invalid dataset fixture | Check `len(svg)`, `svg.lstrip().startswith("<?xml")`/`<svg`, and timeline object | Use `stimulus_timeline_svg`, Agg, and a valid dataset object; write only non-`None` SVG strings |
| Source converter produces malformed JSON | Documentation-specific backtick/column assumptions | Inspect first data row and converter output shape | Do not copy the converter; use explicit pandas schema mapping and record conversion provenance |
| HDF5 result access is locked or incomplete | Concurrent evaluation, stale cache, or file permission issue | Inspect `Results.filepath`, process ownership, and whether evaluation is still running | Stop competing writers, use a separate `hdf5_path`/suffix, preserve user data, and retry only after the writer exits |

## Dependency and network boundaries

Core `Results`, pandas statistics, Matplotlib plots, and fake-dataset timeline
rendering are CPU/offline-capable. Plotly neural signatures, CodeCarbon
emissions, real-dataset metadata, and benchmark result acquisition are
optional or external. Missing optional dependencies are non-blocking for the
core route; a missing required column or invalid metric interpretation is a
blocking analysis error.
