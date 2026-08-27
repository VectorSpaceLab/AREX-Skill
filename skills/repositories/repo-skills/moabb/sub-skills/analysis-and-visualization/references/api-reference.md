# Analysis API reference

Verified against the MOABB inspection package at the source revision used for
this skill. Import public functions from `moabb.analysis`,
`moabb.analysis.meta_analysis`, `moabb.analysis.plotting`,
`moabb.analysis.timeline`, or `moabb.analysis.style` as shown below.

## Result storage and report generation

| API | Signature | Inputs and output |
|---|---|---|
| `Results` | `Results(evaluation_class, paradigm_class, suffix="", overwrite=False, hdf5_path=None, additional_columns=None)` | Creates/opens an HDF5 result store. `evaluation_class` must subclass `BaseEvaluation`; `paradigm_class` must subclass `BaseParadigm`; returns a store object. |
| `Results.to_dataframe` | `to_dataframe(pipelines=None, process_pipeline=None)` | Returns a `pandas.DataFrame`. Pass both `pipelines` and `process_pipeline` for digest filtering, or neither; passing only one raises `ValueError`. |
| `Results.add` | `add(results, pipelines, process_pipeline)` | Adds per-pipeline dict/list results to the HDF5 store. It is evaluation-side storage, not a plotting replacement. |
| `analyze` | `analyze(results, out_path, name="analysis", plot=False)` | `results` is a DataFrame, not a `Results` object; `out_path` must be an existing `str`. Creates `out_path/name`, writes `info.txt`, `data.csv`, `stats.csv`, and with `plot=True` also `scores.pdf` and `ordering.pdf`. |

For an existing store, call `df = store.to_dataframe()` before `analyze` or
any plotting/statistics API. `analyze` records date/system/CPU in `info.txt` and
is therefore not byte-for-byte deterministic across runs.

## Chance-level APIs

| API | Signature | Behavior |
|---|---|---|
| `adjusted_chance_level` | `adjusted_chance_level(n_classes: int, n_trials: int, alpha: float = 0.05) -> float` | Returns `binom.isf(alpha, n_trials, 1/n_classes) / n_trials`. It is a proportion. |
| `chance_by_chance` | `chance_by_chance(data, alpha: float \| list[float] = 0.05) -> dict[str, dict]` | Groups by `dataset`, reads first `n_classes` and `samples_test`, and returns `{dataset: {"theoretical": float, "adjusted": {alpha: float}}}`. |

`score_plot`, `distribution_plot`, and `paired_plot` accept the returned
mapping. They convert scores and chance values to percentages for display.
`chance_level=None` preserves a 0.5 internal reference but does not draw a
chance line; pass a value or `"auto"` to draw one.

## Statistics

| API | Signature | Output |
|---|---|---|
| `collapse_session_scores` | `collapse_session_scores(df)` | DataFrame averaged by `pipeline`, `dataset`, `subject`; numeric columns are averaged. |
| `compute_pvals_wilcoxon` | `compute_pvals_wilcoxon(df, order=None)` | Square one-tailed p-value `ndarray`; `df` has one column per pipeline and paired rows. |
| `compute_pvals_perm` | `compute_pvals_perm(df, order=None, seed=None)` | Square p-value `ndarray`; exact sign permutations for at most 13 rows and 10,000 random permutations above that threshold. Seed it for reproducibility. |
| `compute_effect` | `compute_effect(df, order=None)` | Signed standardized mean-difference matrix (`mean(diff) / std(diff)`). |
| `compute_dataset_statistics` | `compute_dataset_statistics(df, perm_cutoff=20)` | Long DataFrame with `dataset`, `pipe1`, `pipe2`, `p`, `smd`, and `nsub` (plus a reset-index column). Per-dataset rows are session-collapsed first. |
| `find_significant_differences` | `find_significant_differences(df, perm_cutoff=20)` | `(dfP, dfT)`, square DataFrames of combined p-values and effects across datasets. |
| `combine_effects` | `combine_effects(effects, nsubs)` | Subject-count weighted combined effect. |
| `combine_pvalues` | `combine_pvalues(p, nsubs)` | Stouffer combined p-value, or the single value when one dataset is supplied. |

Statistics are paired only where the pivot has both pipeline values for a
unit. Check for missing/duplicate `(dataset, subject, pipeline)` rows before
interpreting a matrix.

## Matplotlib plots

| API | Signature | Output and important parameters |
|---|---|---|
| `score_plot` | `score_plot(data, pipelines=None, orientation="vertical", chance_level=None)` | `(Figure, color_dict)`. `orientation` is `vertical`/`v` or `horizontal`/`h`; input must have result columns. |
| `distribution_plot` | `distribution_plot(data, pipelines=None, orientation="vertical", chance_level=None, figsize=None)` | `(Figure, color_dict)` with violin plus points. |
| `paired_plot` | `paired_plot(data, alg1, alg2, chance_level=None)` | `Figure` of paired pipeline scores by subject/dataset. Both names must exist. |
| `summary_plot` | `summary_plot(sig_df, effect_df, p_threshold=0.05, simplify=True)` | `Figure` heatmap from p-value and effect matrices. It may simplify displayed labels. |
| `meta_analysis_plot` | `meta_analysis_plot(stats_df, alg1, alg2)` | `Figure` from `compute_dataset_statistics`; missing algorithm names raise `ValueError`. |
| `dataset_bubble_plot` | `dataset_bubble_plot(dataset=None, center=(0.0, 0.0), scale=0.5, size_mode="count", shape="circle", gap=0.0, color_map=None, alphas=None, title=True, legend=True, legend_position=None, fontsize=8, ax=None, scale_ax=True, dataset_name=None, paradigm=None, n_subjects=None, n_sessions=None, n_trials=None, trial_len=None)` | `Axes`. With no dataset, all descriptive fields are required; `size_mode` is `count` or `duration`, and `shape` is `circle` or `hexagon`. |
| `codecarbon_plot` | `codecarbon_plot(data, order_list=None, pipelines=None, country="", include_efficiency=False, include_power_vs_score=False)` | `Figure`; requires `carbon_emission` for meaningful plots. |
| `emissions_summary` | `emissions_summary(data, order_list=None, pipelines=None)` | Summary DataFrame or `None` when `carbon_emission` is absent. |

All plot functions return handles; call `fig.savefig(path, bbox_inches="tight")`
and `matplotlib.pyplot.close(fig)` in scripts. Scores are displayed as
percentages by the plotting helpers.

## Timeline and style APIs

| API | Signature | Output |
|---|---|---|
| `TimelinePhase` | `TimelinePhase(label, onset_s, duration_s, style, icon=None)` | Dataclass for one phase. |
| `TimelineAnnotation` | `TimelineAnnotation(start_s, end_s, label)` | Dataclass for a timing brace/annotation. |
| `StimulusTimeline` | `StimulusTimeline(paradigm, dataset_name, phases, annotations, total_duration_s, is_approximate=False, notes=None)` | Dataclass normalized from metadata. |
| `extract_stimulus_timeline` | `extract_stimulus_timeline(dataset)` | `StimulusTimeline`; uses paradigm-specific metadata and a generic fallback. |
| `plot_stimulus_timeline` | `plot_stimulus_timeline(dataset, *, figsize=None, ax=None, show_annotations=True, title=None)` | Matplotlib `Figure`; marks approximate titles when needed. |
| `stimulus_timeline_svg` | `stimulus_timeline_svg(dataset, **kwargs)` | SVG string; forwards kwargs to `plot_stimulus_timeline`. |
| `plot_class_balance` | `plot_class_balance(dataset, *, figsize=None)` | `Figure` or `None` if event/classes are unavailable. |
| `class_balance_svg` | `class_balance_svg(dataset, **kwargs)` | SVG string or `None`. |
| `plot_session_structure` | `plot_session_structure(dataset, *, figsize=None)` | `Figure` or `None` if `n_sessions` is unavailable. |
| `session_structure_svg` | `session_structure_svg(dataset, **kwargs)` | SVG string or `None`. |
| `get_moabb_palette` | `get_moabb_palette(n)` | List of hex colors, cycling for `n` larger than the palette. |
| `set_moabb_defaults` | `set_moabb_defaults()` | Applies global Seaborn/Matplotlib defaults. |
| `apply_moabb_style` | `apply_moabb_style(ax, title="", subtitle="", source=None, accent_line=True, grid_axis="y")` | Mutates an axes/figure with MOABB styling. |
| `style_legend` | `style_legend(ax, **kwargs)` | Restyles an existing legend; no-op without one. |

## Optional Plotly neural signatures

When Plotly is installed, `moabb.analysis` exposes
`generate_neural_signature(dataset, subjects=None, output_dir=None)` and
`neural_signature_html(dataset, subjects=None)`. The generator returns a list
of `Path` objects and writes HTML; it calls a guarded Plotly check and may
need dataset epochs. Treat this as optional and data-dependent, not a core
headless Matplotlib check.
