# CLI reference

The public entry point is `deepdanbooru=deepdanbooru.__main__:main`.
All paths are validated by Click as existing paths before the command body runs.
Use absolute paths in automation when the current directory may change.

## `evaluate`

```console
deepdanbooru evaluate TARGET_PATHS... [OPTIONS]
```

### Model and tag selection

```console
--project-path DIRECTORY
--model-path FILE
--tags-path FILE
```

`--project-path` selects the model named by `project.json` and the project's
`tags.txt`. `--model-path` and `--tags-path` override the corresponding project
components when supplied. The command body requires a project or an explicit
model, and independently requires a project or explicit tags. Thus, in fully
explicit mode, supply both `--model-path MODEL` and `--tags-path TAGS`.

The project model loader searches for `model-MODEL_NAME.keras` and then
`model-MODEL_NAME.h5`, where `MODEL_NAME` is `project.json`'s `model` value.
The direct route sends `--compile` to Keras model loading; the default is
`--no-compile`.

### All `evaluate` options and defaults

| Option | Default | Effect |
|---|---:|---|
| `--project-path DIRECTORY` | none | Select project model/tags, or provide defaults for one direct override. |
| `--model-path FILE` | none | Load this saved Keras model. |
| `--tags-path FILE` | none | Load newline-separated tags from this file. |
| `--threshold FLOAT` | `0.5` | Yield/print scores `>=` this value. |
| `--allow-gpu` | off | Do not set `CUDA_VISIBLE_DEVICES=-1`; does not prove GPU readiness. |
| `--compile / --no-compile` | `--no-compile` | Pass the selected boolean to `load_model`. |
| `--allow-folder` | off | Treat non-file targets as folders and recursively expand them. |
| `--save-txt` | off | Write selected tag names to a sidecar with the same stem. |
| `--folder-filters TEXT` | `*.[Pp][Nn][Gg],*.[Jj][Pp][Gg],*.[Jj][Pp][Ee][Gg],*.[Gg][Ii][Ff]` | Comma-separated `Path.rglob` patterns used only with `--allow-folder`. |
| `--verbose` | off | Print model/tag load messages; also enables more warnings and TensorFlow logging before dispatch. |

The target argument is variadic and may contain files and, with
`--allow-folder`, directories. Without `--allow-folder`, a directory remains
in the target list and later fails as an image input. With folder expansion,
the discovered paths are naturally sorted. A path that is already a regular
file is treated as one target even when `--allow-folder` is present; filters do
not apply to it.

### Output format

For each target, stdout contains:

```text
Tags of /path/to/image.png:
(0.881) 1girl
(0.732) long_hair

```

The score uses Python format `05.3f`, and tag order is the order in `tags.txt`
(or the explicit tags file), not descending score order. Only tags meeting the
threshold are printed. A blank line follows each target.

With `--save-txt`, the command writes `/path/to/image.txt` beside
`image.png` (and similarly replaces any extension for other image names). The
file contains selected tag names separated by `, `, without scores. It does not
create a separate output directory and can overwrite an existing sidecar.

## `evaluate-project`

```console
deepdanbooru evaluate-project PROJECT_PATH TARGET_PATH [--threshold FLOAT]
```

`--threshold` defaults to `0.5`. `PROJECT_PATH` must be a directory and
`TARGET_PATH` may be a file or directory. A target directory is traversed
recursively with these case-insensitive suffix patterns:

```text
*.[Pp][Nn][Gg]
*.[Jj][Pp][Gg]
*.[Jj][Pp][Ee][Gg]
*.[Gg][Ii][Ff]
```

The project route is intended to load the project model and tags and use its
`image_width` and `image_height`. In the exact 1.0.0 source revision, native
`evaluate-project` calls the missing `dd.data.load_tags_from_project` symbol and
raises `AttributeError` before inference. Use `evaluate TARGET --project-path
PROJECT --allow-folder` for a real run; that supported route loads tags from the
available project API. The bundled `evaluate_project_smoke.py` exercises this
fallback and does not claim an unverified native run.

Native `evaluate-project` has no `--allow-folder`, `--folder-filters`,
`--save-txt`, `--compile`, `--allow-gpu`, or `--verbose` option. If a corrected
package or reviewed local native compatibility fix is used, record the package
version/source commit because this skill covers the 1.0.0 snapshot and version
drift may change the behavior.

## Related commands

Use [project-data-setup](../../project-data-setup/SKILL.md) for
`create-project`, tag files, and dataset preparation. Use
[post-training-tools](../../post-training-tools/SKILL.md) for `conv2tflite` and
`grad-cam`; neither replaces ordinary evaluation.
