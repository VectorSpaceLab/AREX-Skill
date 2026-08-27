# Configuration and Output Troubleshooting

## `minimal` plus config file

Symptom: `Arguments config_file and minimal are mutually exclusive.`

Fix: use either the built-in minimal preset or a YAML file. To customize minimal
behavior, generate a minimal-style YAML and omit `minimal=True` / `--minimal`.

## Environment variables do not apply

Settings read environment variables with the `PROFILE_` prefix. Use assignment,
not function-call syntax:

```python
import os
os.environ["PROFILE_TITLE"] = "My Custom Profiling Report"
os.environ["PROFILE_PLOT"] = '{"dpi": 1000}'
```

If a variable contains a nested settings object, provide valid JSON.

## Stale field names from old docs

Use current source field names. For categorical frequency plots, use
`plot.cat_freq`, not stale `plot.pie` naming.

## Missing HTML assets

If `html.inline=False`, the package writes an assets directory next to the HTML
file. Move that directory together with the HTML. If report consumers need a
single artifact, set `html.inline=True`.

## Config changes do not show up

Rendered outputs are cached. Use:

```python
profile.invalidate_cache()
```

or create a new `ProfileReport` after changing configuration.

## Serialization load fails

`ProfileReport.load()` checks the DataFrame hash. Load into a report with the
same DataFrame or into an empty/lazy report when you only need stored output.

## Pillow warning during export

The package warns if the installed Pillow version is older than 9.5. Upgrade
Pillow in the environment if image export fails or warning noise matters.

## Invalid enum or plot values

Theme, image format, and categorical plot values are validated while rendering.
Use known values such as `theme="united"`, `theme="flatly"`,
`plot={"image_format": "png"}`, and `plot={"cat_freq": {"type": "bar"}}`.
Invalid categorical frequency plot types such as `scatter` or `box` raise a
render-time error.
