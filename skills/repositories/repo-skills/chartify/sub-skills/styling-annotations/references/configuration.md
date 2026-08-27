# Configuration

Chartify reads config files from `CHARTIFY_CONFIG_DIR` when the environment variable is set. Set it before importing `chartify`, and make sure the value ends with a path separator because Chartify concatenates file names as plain strings.

If the variable is unset, Chartify falls back to a `~/.chartify/`-style directory under the current user's home path.

## Config file map

| File | Loader behavior | Purpose | Trust level |
| --- | --- | --- | --- |
| `options_config.yaml` | `yaml.UnsafeLoader` | Overrides default option values such as palette names and `chart.blank_labels`. | Trusted only. |
| `style_settings_config.yaml` | `yaml.safe_load` | Overrides chart, legend, subtitle, interval, line, and second-axis style settings. | Safe YAML. |
| `colors_config.yaml` | `yaml.UnsafeLoader` | Adds or renames custom color-name mappings. | Trusted only. |
| `color_palettes_config.yaml` | `yaml.SafeLoader` | Registers custom palette definitions. | Safe YAML. |

## Path rules

- `CHARTIFY_CONFIG_DIR` must end with a separator such as `/` on Unix-like systems.
- If the directory exists but a file is missing, Chartify falls back to built-in defaults for that file.
- If you change `CHARTIFY_CONFIG_DIR` in an already-running session, reload the Chartify modules or start a fresh process before constructing new charts.
- The options file is read first, so it can redirect the other config-file paths.

## Trusted sample files

Use the sample formats below when you need a local config directory for annotation and style work.

### `options_config.yaml`

This file uses `OptionValue` objects inside an ordered mapping.

```yaml
!!python/object/apply:collections.OrderedDict
- - - style.color_palette_categorical
    - !!python/object:chartify._core.options.OptionValue
      value: Category20
  - - style.color_palette_sequential
    - !!python/object:chartify._core.options.OptionValue
      value: Blues
  - - style.color_palette_diverging
    - !!python/object:chartify._core.options.OptionValue
      value: RdBu
  - - style.color_palette_accent
    - !!python/object:chartify._core.options.OptionValue
      value: Category20
  - - style.color_palette_accent_default_color
    - !!python/object:chartify._core.options.OptionValue
      value: grey
```

### `style_settings_config.yaml`

This file is plain YAML and safe to parse with `safe_load`.

```yaml
chart:
  figure.background_fill_color: white
  figure.xgrid.grid_line_color: null
  figure.ygrid.grid_line_color: null
legend:
  figure.legend.location: top_right
  figure.legend.orientation: horizontal
subtitle:
  subtitle_align: left
  subtitle_text_color: "#666666"
  subtitle_location: above
```

### `colors_config.yaml`

This file uses tuple keys and is loaded with `UnsafeLoader`, so only use it for trusted content.

```yaml
? !!python/tuple
- 232
- 232
- 232
: Light Grey
? !!python/tuple
- 83
- 88
- 95
: Dark Grey
```

### `color_palettes_config.yaml`

This file is a safe YAML list of `[colors, palette_type, name]` triples.

```yaml
- - - '#5ff550'
    - '#fae62d'
    - '#f037a5'
  - categorical
  - Sample Accent
- - - '#2c7fb8'
    - '#7fcdbb'
    - '#edf8b1'
  - sequential
  - Sample Sequential
```

## Runtime reminders

- `style_settings_config.yaml` values are stored on the `Style` object and applied when chart construction or legend application consumes them.
- `colors_config.yaml` can shadow built-in color names if you reuse an existing name.
- `color_palettes_config.yaml` palette names are case-insensitive in the registry.
- Only load files from a trusted source; `options_config.yaml` and `colors_config.yaml` can execute arbitrary YAML payloads because they use `yaml.UnsafeLoader`.
