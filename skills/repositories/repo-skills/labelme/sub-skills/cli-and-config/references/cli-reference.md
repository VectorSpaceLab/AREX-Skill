# CLI Reference

## Basic commands

```bash
labelme --help
labelme --version
labelme                     # open the GUI without an initial target
labelme image.jpg           # annotate one image
labelme image.json          # open an existing Annotation File
labelme image_directory/    # annotate a directory of images
```

## Supported flags in this checkout

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--version`, `-V` | Print app/version and exit | Safe headless check. |
| `--reset-config` | Clear Qt Window State | Does not rewrite the YAML Config File. |
| `--logger-level {debug,info,warning,error,critical}` | Set loguru logging threshold | `fatal` is rejected by argparse. |
| positional `path` | Image file, Annotation File, or directory | Optional. |
| `--output OUTPUT` | Output directory for Annotation Files | This repo rejects `.json` paths for `--output`; use a directory. |
| `--config CONFIG` | Config File path or inline YAML mapping | Missing explicit file exits; missing default file falls back to defaults. |
| `--with-image-data` | Embed image bytes in each JSON | Increases JSON size but makes Annotation File portable. |
| `--no-auto-save` | Disable automatic saving | Overrides Config for the session. |
| `--no-sort-labels` | Preserve supplied label order | Deprecated alias `--nosortlabels` warns. |
| `--flags FLAGS` | Image-level Flags from comma list or file | Flags are not Shape Labels. |
| `--label-flags LABEL_FLAGS` | YAML mapping from label patterns to per-Shape Flags | Deprecated alias `--labelflags` warns. |
| `--labels LABELS` | Label List from comma list or file | Required when `--validate-label exact` is active. |
| `--validate-label exact` | Reject labels outside the Label List | Deprecated alias `--validatelabel` warns. |
| `--keep-prev` | Start next image from previous annotation | Useful for video/frame sequences. |
| `--epsilon EPSILON` | Canvas hit-test tolerance | Use only for precise editing behavior. |

## Annotation session patterns

### Fixed label vocabulary

```bash
labelme images/ --labels labels.txt --validate-label exact --no-sort-labels
```

`labels.txt` should contain one label per line. Use `--no-sort-labels` when the
order has UI meaning.

### Image-level classification / cleaning

```bash
labelme images/ --flags flags.txt
```

This configures image-level Flags, not Shape Labels. See the annotation-data
sub-skill if the task is to consume the resulting JSON.

### Per-shape attributes

```bash
labelme images/ --labels labels.txt --label-flags '{.*: [occluded, truncated], person: [male]}'
```

The value is YAML. Keep pattern strings quoted when they include characters YAML
could interpret.

### Inline Settings override

```bash
labelme images/ --config '{shape_color: {mode: auto, auto: {shift: -2}}}'
```

Inline mappings are session overrides and are not writable through the Settings
dialog. Use a file path for editable persistent settings.

## Output path behavior

- `--output some_dir` writes Annotation Files to a directory.
- A path ending in `.json` is rejected by this checkout for `--output` because
  one session path can contain multiple images.
- When `--with-image-data` is absent, JSON usually stores an external `imagePath`.
  Keep images next to or reachable from the JSON if future consumers need them.

## Headless checks

Use these before any GUI or e2e run:

```bash
labelme --help
labelme --version
python -m labelme --help
```

If these pass but the GUI fails, the problem is likely display/Qt/platform setup
rather than argparse or package installation.
