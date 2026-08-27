# Configuration

## Files and sources

- Default Config: shipped with the package as `labelme/_config/default_config.yaml`.
- User Config File: `~/.labelmerc` by default.
- Alternative Config File: pass a path with `--config <path>`.
- Inline session overrides: pass a YAML mapping string with `--config '{...}'`.
- CLI flags such as `--labels`, `--flags`, `--with-image-data`, and
  `--no-auto-save` become session overrides.

The Config File stores sparse Overrides. Setting a value back to its default
removes that Override; empty parent sections are pruned. Comment-preserving
writes are handled with ruamel.yaml.

## Important groups

| Group | Common keys | Notes |
| --- | --- | --- |
| Appearance and language | `color_theme`, `language` | `system`, `light`, `dark`; language takes effect after restart. |
| Files and saving | `auto_save`, `with_image_data` | `with_image_data` embeds image bytes in JSON. |
| Drawing and canvas | `display_label_popup`, `canvas.allow_out_of_bounds_points`, `shape.show_labels` | Out-of-bounds points are opt-in. |
| Continue between images | `keep_prev`, `keep_prev_scale`, `keep_prev_brightness_contrast` | Useful for frame/video annotation. |
| Label sources | `labels`, `flags` | Lists are YAML sequences. |
| Label behavior | `validate_label`, `sort_labels`, `label_completion` | `validate_label: exact` requires non-empty labels. |
| AI assist | `ai.default`, `ai.suppress_existing_shape_matches` | Prompt compatibility still must be enforced at runtime. |

## YAML examples

Persistent Config File snippet:

```yaml
auto_save: true
with_image_data: false
labels: [cat, dog, person]
validate_label: exact
sort_labels: false
shape_color:
  mode: auto
  auto:
    shift: -2
canvas:
  allow_out_of_bounds_points: true
ai:
  default: Sam2 (balanced)
  suppress_existing_shape_matches: false
```

Inline equivalent for a one-off session:

```bash
labelme images/ --config '{labels: [cat, dog, person], validate_label: exact, sort_labels: false}'
```

## Migration and validation behavior

- Legacy `store_data` migrates to `with_image_data`.
- Legacy `logger_level` is removed from Config; it is now CLI-only.
- Legacy `SegmentAnything (...)` AI model names migrate to `Sam (...)`.
- Legacy polygon shortcut names migrate to Shape names (`edit_shape`,
  `delete_shape`, etc.).
- Malformed sections such as `shortcuts: oops` or `ai: oops` raise a config
  validation error instead of silently replacing nested defaults with scalars.
- Duplicate `labels` values are rejected.
- `validate_label: exact` with empty labels is rejected.

## Settings dialog behavior

- Settings apply immediately; there is no OK/Apply/Cancel workflow.
- Failed writes revert the edited control to the last saved value.
- The dialog is disabled when the active session has CLI or inline YAML
  overrides that cannot be written back to a file.
- Chrome colors follow the Qt palette; annotation Shape colors are data and stay
  fixed across light/dark theme changes.

## Helper

Run the bundled inspector to check a file or inline mapping using installed
labelme validation rules:

```bash
python sub-skills/cli-and-config/scripts/inspect_labelme_config.py --config-yaml '{labels: [cat], validate_label: exact}' --show labels
python sub-skills/cli-and-config/scripts/inspect_labelme_config.py --config-file ~/.labelmerc --show ai
```
