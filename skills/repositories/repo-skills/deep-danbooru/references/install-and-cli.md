# Installation and CLI reference

Read this when choosing an install variant, checking the public entry point, or
constructing a command across sub-skills.

## Package facts

- Distribution: `deepdanbooru`
- Skill-covered version: `1.0.0`
- Python source package: `deepdanbooru`
- Console entry point: `deepdanbooru=deepdanbooru.__main__:main`
- Required base families from `setup.py`: Click, NumPy, requests, scikit-image,
  and six.
- TensorFlow workflow requirements from `requirements.txt` and the README:
  TensorFlow and TensorFlow I/O. The source imports both on normal package/CLI
  paths, so a base install without those packages is not enough for this
  workflow graph.

The repository metadata and README have different minimum versions: `setup.py`
contains older compatibility floors while the current README/requirements list
newer floors. Prefer the requirements documented by the checkout being used,
and verify with `python scripts/environment_smoke.py` before a real workflow.

## Command map

| Command | Purpose | Main inputs | Important boundaries |
|---|---|---|---|
| `create-project PROJECT` | Write default `project.json` | new/existing directory | Does not create tags, database, images, or model |
| `download-tags PROJECT` | Fetch General/Character tags and system tags | Danbooru credentials, network | Credentialed network; opt-in only |
| `make-training-database SOURCE OUTPUT` | Filter/copy SQLite posts and append rating tags | source SQLite, separate output | Source/output must differ; optional overwrite/vacuum |
| `evaluate-project PROJECT TARGET` | Evaluate using project artifacts | project, image/file/folder | Native 1.0.0 route has a tag-loader defect; use `evaluate TARGET --project-path PROJECT --allow-folder` for production and do not claim an unverified native run. |
| `grad-cam PROJECT TARGET OUTPUT` | Experimental attribution maps | project, target, output directory | One gradient pass per selected tag; writes images |
| `evaluate TARGET...` | Predict tags | project or model+tags, files/folders | Project-backed folder inference uses `--allow-folder`; CPU by default |
| `conv2tflite` | Convert saved Keras model | project or model, save path | At least one optimization flag required |

## Command construction rules

- Run `deepdanbooru COMMAND --help` in the target environment before copying
  flags into automation; Click help is a safe parser check.
- Keep paths quoted when they contain spaces. Use absolute or intentionally
  portable paths consistently within one project.
- Never put Danbooru API keys in a generated command, fixture, report, or shell
  history. Prefer an interactive secret mechanism supplied by the user's
  environment.
- A successful CLI help import proves package/CLI dependencies only; it does
  not prove a model can load, an image can decode, or a GPU is usable.
