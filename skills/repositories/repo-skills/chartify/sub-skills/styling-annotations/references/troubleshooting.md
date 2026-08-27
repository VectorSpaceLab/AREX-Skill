# Troubleshooting

Use this matrix when styling, annotation, or config-driven behavior does not match the chart you expected.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: Invalid color palette name` | The palette is not in the global registry or the name is misspelled. | Check the case-insensitive registry name, register the palette with `create_palette(...)`, or pick a built-in name from `chartify.color_palettes`. |
| `CHARTIFY_CONFIG_DIR` seems ignored | The env var is missing, set after import, or missing the trailing path separator. | Set `CHARTIFY_CONFIG_DIR="/path/to/config/"` before importing `chartify`. |
| Config files load from defaults instead of your files | The config directory or individual YAML files do not exist. | Create the directory tree and write the four expected filenames, or run the sample-config helper script. |
| You are worried about config safety | `options_config.yaml` and `colors_config.yaml` use `yaml.UnsafeLoader`. | Only load trusted YAML from a controlled source. Do not accept untrusted config payloads. |
| Tick labels rotate in a confusing way | Grouped categorical axes interpret orientation per hierarchy level, not per plot series. | Pass a list to the orientation setter and remember that `horizontal`, `vertical`, and `diagonal` map differently on x and y axes. |
| Factor order does not change | Plot-time ordering still wins, or the factor setter was not used on the correct axis. | Use `categorical_order_by` / `categorical_order_ascending` on the plot call, or override with `set_xaxis_factors(...)` / `set_yaxis_factors(...)` after plotting. |
| Datetime callouts land in the wrong place | The x-side value was not datetime-like, or the wrong orientation was used for a span. | Pass strings or `pd.Timestamp` values for datetime x coordinates. For a vertical line on a datetime x axis, use `orientation="height"`. |
| Style values appear in `style.settings` but not on the figure | The chart has not yet applied the chart settings, or you changed config after the chart was created. | Start a new chart after updating config, or reload the Chartify modules before constructing the chart. |
| Legend placement appears to do nothing | No legend existed yet when you moved it. | Plot grouped or color-separated data first, then call `set_legend_location(...)`. |
| `expand_palette(...)` looks flat or errors | The base palette is too small for interpolation. | Start from a palette with at least two colors, or create a richer palette before expanding it. |

## Quick checks

- `hide_xaxis()` and `hide_yaxis()` leave labels visible until you clear them explicitly.
- For datetime axes, use tick formats such as `%Y-%m` rather than numeric format strings.
- Use `set_subtitle("")` to clear the subtitle.
- If stacked-series legend order looks reversed, remember that vertical legend placement reverses the stack order on purpose.
