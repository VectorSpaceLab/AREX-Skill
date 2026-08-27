# Optional EDA report tools

The minimum verified environment covers import, file loading, DataFrame summaries, `describe_dataset`, SQL safety elsewhere, and Streamlit version checks. The optional EDA report tools in this sub-skill were inspected from source but were not fully executed in the minimum environment because they need additional libraries and may write reports, render plots, or launch services.

## Capability matrix

| Tool | Extra dependency | Side effects | Safe default | Use when | Avoid when |
| --- | --- | --- | --- | --- | --- |
| `visualize_missing` | `missingno` plus Matplotlib stack | Generates base64-encoded PNG plots in memory. | Use bounded `n_sample` for large data. | User asks for missingness matrix/bar/heatmap and plotting deps are installed. | Dataset is huge and unsampled, plotting stack is unavailable, or image artifacts are not desired. |
| `generate_correlation_funnel` | `pytimetk` plus plotting/Plotly stack | Binarizes data; attempts static and Plotly plots in memory. | Specify target and target level; inspect artifact for plot errors. | User needs correlation funnel style target screening. | Target column or target level is ambiguous, high-cardinality columns would explode one-hot features, or optional deps are unavailable. |
| `generate_sweetviz_report` | `sweetviz` | Writes an HTML report file; may create a default report directory if none is supplied. | Pass a caller-approved `report_directory`, keep `open_browser=False`, keep `include_html=False` unless the caller wants embedded HTML. | User explicitly wants a Sweetviz HTML report. | Automation cannot write report files, Sweetviz is not installed, or browser opening is unsafe. |
| `generate_dtale_report` | `dtale` (not part of the package's declared `data_science` extra) | Starts a local interactive D-Tale service. | Require explicit approval; keep `host="localhost"` and `open_browser=False`. | User wants an interactive local data explorer and accepts a running service. | Non-interactive/CI runs, untrusted multi-user host, occupied port, or no approval for a service launch. |

## Dependency guidance

- The package declares a `data_science` extra for `pytimetk`, `missingno`, and `sweetviz`.
- `dtale` is imported by `generate_dtale_report` but is not included in the declared `data_science` extra; install it separately only when the user selects D-Tale.
- Optional plotting/report dependencies can be heavy. Do not install optional extras for a simple `describe_dataset` or `get_dataframe_summary` task.
- If optional dependencies are missing, present the exact tool-specific missing package rather than retrying with broad install commands.

## `visualize_missing` workflow

```python
from ai_data_science_team.tools.eda import visualize_missing

content, artifact = visualize_missing.func(
    data_raw=df.to_dict(),
    n_sample=min(len(df), 1000),
)

matrix_png_b64 = artifact["matrix_plot"]
bar_png_b64 = artifact["bar_plot"]
heatmap_png_b64 = artifact["heatmap_plot"]
```

Recovery notes:

- If `missingno` is not installed, install the optional EDA dependency set or choose `describe_dataset` instead.
- If sampling fails because `n_sample` is larger than the DataFrame length, pass `min(len(df), desired_sample)`.
- If plotting is slow or unreadable, reduce `n_sample` or summarize missing percentages with pandas instead.

## `generate_correlation_funnel` workflow

```python
from ai_data_science_team.tools.eda import generate_correlation_funnel

content, artifact = generate_correlation_funnel.func(
    data_raw=df.to_dict(),
    target="Churn",
    target_bin_index="Yes",
    corr_method="pearson",
    n_bins=4,
    thresh_infreq=0.01,
)

correlation_data = artifact["correlation_data"]
plot_image = artifact["plot_image"]
plotly_figure = artifact["plotly_figure"]
```

Recovery notes:

- The tool searches one-hot encoded columns beginning with `target + "__"`. If a target level is wrong, it falls back to a matching/default target level. Tell the user which level was used from the returned content.
- Static or Plotly plotting can fail independently of the correlation calculation. Inspect `artifact["plot_image"]` and `artifact["plotly_figure"]`; either may be an error dictionary.
- For high-cardinality categoricals, raise `thresh_infreq`, reduce columns before calling, or use a simpler statistical summary.

## `generate_sweetviz_report` workflow

```python
from pathlib import Path
from ai_data_science_team.tools.eda import generate_sweetviz_report

report_dir = Path("reports/eda").resolve()
report_dir.mkdir(parents=True, exist_ok=True)

content, artifact = generate_sweetviz_report.func(
    data_raw=df.to_dict(),
    target=None,
    report_name="sweetviz_report.html",
    report_directory=str(report_dir),
    open_browser=False,
    include_html=False,
)

report_file = artifact["report_file"]
```

Recovery notes:

- Always set a caller-approved `report_directory` in automation so files are not written to an unexpected default location.
- Keep `open_browser=False` unless the user is in an interactive desktop session and requests browser opening.
- `include_html=True` can return a very large artifact; avoid it unless the caller explicitly needs embedded HTML.

## `generate_dtale_report` workflow

```python
from ai_data_science_team.tools.eda import generate_dtale_report

content, artifact = generate_dtale_report.func(
    data_raw=df.to_dict(),
    host="localhost",
    port=40000,
    open_browser=False,
)

url = artifact["dtale_url"]
```

Recovery notes:

- Confirm that starting a local service is acceptable before running this tool.
- If the port is occupied, choose another high local port.
- Do not expose D-Tale on a public interface for sensitive data. Keep `host="localhost"` unless the user has explicitly approved a different binding and understands the security risk.

## Default fallback when optional EDA is unavailable

If the user asks for EDA but optional dependencies are unavailable, provide a useful baseline with:

```python
from ai_data_science_team.tools.dataframe import get_dataframe_summary
from ai_data_science_team.tools.eda import describe_dataset

text_summary = get_dataframe_summary(df, n_sample=10, skip_stats=False)[0]
content, describe_artifact = describe_dataset.func(data_raw=df.to_dict())
```

Then explain which optional tool was skipped and what dependency or approval is needed to run it.
