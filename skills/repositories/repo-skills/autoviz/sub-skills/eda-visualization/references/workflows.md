# EDA visualization workflows

## DataFrame workflow

```python
import pandas as pd
from autoviz import AutoViz_Class

AV = AutoViz_Class()
dft = AV.AutoViz(
    "",
    sep=",",
    depVar="",
    dfte=df,
    header=0,
    verbose=1,
    lowess=False,
    chart_format="svg",
    max_rows_analyzed=150000,
    max_cols_analyzed=30,
    save_plot_dir=None,
)
```

Use this route when the user already has a DataFrame. Passing `filename=""` and `dfte=df` avoids file parsing and lets AutoViz work with an in-memory dataset.

## File workflow

```python
from autoviz import AutoViz_Class

AV = AutoViz_Class()
dft = AV.AutoViz(
    "data.csv",
    sep=",",
    depVar="target",
    dfte=None,
    header=0,
    verbose=2,
    lowess=False,
    chart_format="png",
    max_rows_analyzed=50000,
    max_cols_analyzed=30,
    save_plot_dir="autoviz-output",
)
```

Use this route for CSV/TXT/Excel-like file inputs. `sep` applies to CSV/TXT parsing. `header=0` means the first row is the header.

## What AutoViz does internally

1. Loads the file or copies the DataFrame.
2. Samples rows if the input exceeds `max_rows_analyzed`.
3. Classifies columns as continuous, categorical, boolean, date, ID, discrete string, or NLP-like text.
4. Infers problem type from `depVar` when a target is present.
5. Runs a data-quality report through `data_cleaning_suggestions`.
6. Draws plot families such as scatter, pair scatter, distribution, violin, heatmap, date/time, bar, pivot, catscatter, and wordcloud where applicable.

## Target variable rules

- Use `depVar=""` or `None` for unsupervised EDA.
- Use a string column name for supervised EDA.
- If a list is passed, AutoViz selects the first target because multi-label visualization is not directly supported.
- If `depVar` is missing from the DataFrame, AutoViz can return early; verify spelling before debugging plots.

## Large-data controls

- `max_rows_analyzed` limits rows and triggers sampling.
- `max_cols_analyzed` limits the number of variables. For supervised problems with many predictors, AutoViz can use XGBoost to select important features.
- Disable `lowess` for large datasets because regression-line smoothing can be slow.

## Output controls

- `verbose=0`: quieter output.
- `verbose=1`: more printed information and display attempts.
- `verbose=2`: save plots locally without display.
- `save_plot_dir`: destination for saved plots; if omitted, AutoViz uses `AutoViz_Plots` under the current working directory.
