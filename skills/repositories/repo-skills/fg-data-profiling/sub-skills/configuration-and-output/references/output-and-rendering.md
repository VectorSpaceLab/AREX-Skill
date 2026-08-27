# Output and Rendering

## HTML files

```python
profile.to_file("report.html")
```

By default, HTML is inline: CSS, JavaScript, and images are embedded in one
portable file. For external assets:

```python
profile = ProfileReport(df, html={"inline": False}, minimal=True)
profile.to_file("report.html")
```

This creates a sibling assets directory named from the output stem. Keep that
assets directory with the HTML file when moving or publishing the report.

## JSON files

```python
profile.to_file("report.json")
json_text = profile.to_json()
```

The JSON output includes profile metadata, table statistics, variables, alerts,
missing data, samples, duplicates, correlations, scatter data, and package
information. Use JSON for automation, monitoring, or downstream validation.

## Image format and assets

The default plot image format is SVG. Switch to PNG with:

```python
profile = ProfileReport(df, plot={"image_format": "png"})
```

If `html.use_local_assets=False` with non-inline output, fewer local CSS/JS
assets are written because some resources come from a CDN. Use local assets for
offline or air-gapped environments.

## Themes and colors

Theme values are enum-like strings such as `united`, `flatly`, `cosmo`, and
`simplex`.

```python
profile = ProfileReport(
    df,
    minimal=True,
    html={
        "style": {
            "theme": "united",
            "primary_colors": ["#0d6efd", "#dc3545", "#198754"],
        }
    },
)
```

Avoid copying large base64 logos into reusable examples. If a user needs a logo,
accept a data URI or file-to-data-URI conversion in their project code.

## Notebook displays

- `profile.to_notebook_iframe()` displays an HTML iframe and is the most
  portable notebook path.
- `profile.to_widgets()` displays the widget UI and requires notebook/widget
  dependencies.
- `profile._repr_html_()` calls the iframe path for rich notebook display.

If widgets render as plain text, route to optional dependency troubleshooting.

## Browser behavior

`profile.to_file(path, silent=False)` may open the file in a browser or trigger
Colab download behavior. Use `silent=True` (the default in the API) and CLI
`--silent` in automated jobs.

## File suffix behavior

- `.json` writes JSON.
- `.html` writes HTML.
- Other suffixes are treated as HTML with a warning and the suffix is changed to
  `.html`.

## Validating output

For a tiny check:

```python
profile = ProfileReport(df, minimal=True, progress_bar=False)
profile.to_file("check.html")
assert Path("check.html").exists()
profile.to_file("check.json")
assert Path("check.json").exists()
```

When `html.inline=False`, also assert the assets directory exists.
