# AutoViz API reference

This is a distilled reference for the public and semi-public functions most useful to agents. It is not a full source listing.

## Public imports

```python
from autoviz import AutoViz_Class, FixDQ, data_cleaning_suggestions
```

Importing `autoviz` prints a banner with example usage in this repository version.

## `AutoViz_Class.AutoViz`

```python
AutoViz_Class.AutoViz(
    self,
    filename: str,
    sep=',',
    depVar='',
    dfte=None,
    header=0,
    verbose=1,
    lowess=False,
    chart_format='svg',
    max_rows_analyzed=150000,
    max_cols_analyzed=30,
    save_plot_dir=None,
)
```

Key behavior:
- If `dfte` is a pandas DataFrame, AutoViz uses it and replaces `filename` internally.
- If `depVar` is a list, AutoViz selects the first item because it cannot visualize multi-label targets directly.
- `chart_format` routes to `AutoViz_Holo` for `bokeh`, `server`, `bokeh_server`, `bokeh-server`, and `html`; all other listed static formats use `AutoViz_Main`.
- The return value is the DataFrame that AutoViz analyzed, often sampled or column-filtered according to configuration.

## `AutoViz_Class.AutoViz_Main`

```python
AutoViz_Class.AutoViz_Main(
    self,
    filename: str,
    sep=',',
    dep_var='',
    header=0,
    verbose=0,
    lowess=False,
    chart_format='svg',
    max_rows_analyzed=150000,
    max_cols_analyzed=30,
    save_plot_dir=None,
)
```

This is the static matplotlib/seaborn implementation. It loads data, classifies variables, runs data-quality suggestions, draws plots by problem type, and optionally runs wordclouds for discrete string variables.

## `AutoViz_Holo.AutoViz_Holo`

```python
AutoViz_Holo(
    filename,
    sep=',',
    depVar='',
    header=0,
    verbose=0,
    lowess=False,
    chart_format='svg',
    max_rows_analyzed=150000,
    max_cols_analyzed=30,
    save_plot_dir=None,
)
```

This is the interactive HoloViews/Bokeh implementation. It imports `hvplot`, `holoviews`, `panel`, `bokeh`, and related display hooks lazily through `ensure_hvplot_imported()`.

## Data-quality APIs

```python
FixDQ(
    quantile=0.87,
    cat_fill_value='missing',
    num_fill_value=9999,
    rare_threshold=0.01,
    correlation_threshold=0.9,
)

data_cleaning_suggestions(df, target=None)
```

`FixDQ` subclasses `pandas_dq.Fix_DQ`. `data_cleaning_suggestions` requires a pandas DataFrame and calls `pandas_dq.dq_report(data=df, target=target, html=False, csv_engine="pandas", verbose=1)`.

## Data loading and classification helpers

```python
load_file_dataframe(dataname, sep=',', header=0, nrows=None, parse_dates=False)
classify_print_vars(filename: str, sep, max_rows_analyzed, max_cols_analyzed, depVar='', header=0, verbose=0)
analyze_problem_type(train, target, verbose=0)
```

`load_file_dataframe` handles DataFrame inputs directly and file inputs for CSV, Excel, and text-like paths. `classify_print_vars` returns a tuple containing the analyzed DataFrame, target variable, ID columns, boolean columns, categorical columns, continuous variables, string variables, date variables, classes, problem type, and selected columns.

## Text and wordcloud helpers

```python
draw_word_clouds(dft, each_string_var, chart_format, plotname, dep, problem_type, classes, mk_dir, verbose=0)
```

AutoViz's NLP module also includes helpers for contractions, URLs, HTML, emoji removal/conversion, punctuation, stopwords, lemmatization, and word counting. Use the text sub-skill for when and why those helpers are triggered.
