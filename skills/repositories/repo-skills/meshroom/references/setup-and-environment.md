# Meshroom Setup and Environment

## When to Read

Read this before installing Meshroom from source, checking imports, launching the UI, loading plugins, or deciding whether an observed failure is in Meshroom itself versus an optional external dependency.

## Supported Runtime Shape

- Meshroom is a Python package with a PySide6/QML UI and several Python CLI entry points.
- Supported project guidance targets Python 3.9-3.11. Prefer 3.11 for current Linux test work unless a dependency or CI target requires 3.9.
- Runtime requirements are `psutil`, `PySide6`, `markdown`, `requests`, and `pyseq`.
- Development/testing adds `cx_Freeze`, `numpy`, and `pytest`.
- The package version is exposed as `meshroom.__version__`; development builds append `+develop`.

## Source Checkout Installation

For a local source checkout:

```bash
python -m pip install -r requirements.txt
python -m pip install -r dev_requirements.txt  # only when running tests/packaging checks
python -m pip install -e . --no-build-isolation --config-settings editable_mode=compat
python -c "import meshroom; print(meshroom.__version__)"
```

Why `--no-build-isolation` and `editable_mode=compat` may matter:

- `setup.py` imports `cx_Freeze` at module import time for packaging metadata. If editable install builds in isolation without `cx_Freeze`, the setup hook can fail before the package is installed.
- Some editable-install modes can leave distribution metadata present while `import meshroom` fails from a neutral current working directory. The compatibility editable mode makes the package importable for inspection and CLI use.

If a normal installed wheel or release archive is used, follow the release's documented launcher paths instead of source-checkout commands.

## Minimal Import Smoke

Use the root helper:

```bash
python scripts/check_meshroom_runtime.py --cli-help
```

Or run manually:

```bash
python -c "import meshroom, meshroom.core, meshroom.core.desc; print(meshroom.__version__)"
python -c "import meshroom; meshroom.setupEnvironment(); import meshroom.core; meshroom.core.initNodes(); print(len(meshroom.core.pluginManager.getNodeDescProviders()))"
```

A healthy base framework import discovers built-in nodes from `meshroom/nodes`. External plugin nodes appear only after their plugin/template paths are configured.

## Environment Variables

Meshroom centralizes environment variables in `meshroom.env.EnvVar`.

| Variable | Purpose |
| --- | --- |
| `MESHROOM_PLUGINS_PATH` | Additional plugin roots. Each plugin root should contain a `meshroom/` subfolder. |
| `MESHROOM_USER_PLUGINS_PATH` | User plugin roots; loaded similarly but node version type is treated as user-owned. |
| `MESHROOM_NODES_PATH` | Additional node package folders loaded with built-in nodes. |
| `MESHROOM_SUBMITTERS_PATH` | Additional submitter package folders. |
| `MESHROOM_PIPELINE_TEMPLATES_PATH` | Extra folders of `.mg` pipeline templates. |
| `MESHROOM_REZ_PLUGINS`, `MESHROOM_USER_REZ_PLUGINS` | Rez package mappings for plugin roots. |
| `MESHROOM_TEMP_PATH` | Temporary project path root for generated scene files. |
| `MESHROOM_VERBOSE` | CLI and runtime log level: `fatal`, `error`, `warning`, `info`, `debug`, `trace`. |
| `MESHROOM_DEFAULT_PIPELINE` | Default pipeline name used by batch/UI startup when present. |
| `MESHROOM_DEFAULT_SUBMITTER` | Default UI submitter name. |
| `MESHROOM_SUBMIT_LABEL` | Default submitted job label format. |
| `MESHROOM_QML_DEBUG`, `MESHROOM_QML_DEBUG_PARAMS` | Enable QML debugging for UI sessions. |
| `MESHROOM_OUTPUT_QML_WARNINGS` | Route QML warnings through logging so hidden load errors become visible. |
| `MESHROOM_INSTANT_CODING` | Enables QML live file watching/reload in development. |

## External AliceVision / QtAliceVision

Meshroom's flagship photogrammetry workflows rely on external AliceVision binaries and data. For those workflows, configure at least:

```bash
export ALICEVISION_ROOT=/path/to/AliceVision/install
export MESHROOM_NODES_PATH="$ALICEVISION_ROOT/share/meshroom${MESHROOM_NODES_PATH:+:$MESHROOM_NODES_PATH}"
export MESHROOM_PIPELINE_TEMPLATES_PATH="$ALICEVISION_ROOT/share/meshroom${MESHROOM_PIPELINE_TEMPLATES_PATH:+:$MESHROOM_PIPELINE_TEMPLATES_PATH}"
```

`meshroom.setupEnvironment()` also looks for AliceVision resource files under an installed standalone layout and can populate defaults such as sensor database and voctree paths when they exist.

QtAliceVision is optional for richer UI visualization. If installed, add its QML/plugin directories through `QML2_IMPORT_PATH` and `QT_PLUGIN_PATH` as documented by the plugin.

## UI Launch

From source, launch the UI with one of:

```bash
PYTHONPATH=$PWD python meshroom/ui
./start.sh
```

Full UI launch can require a display server, OpenGL/native drivers, and QML Scene3D modules. For headless validation, prefer importing `meshroom.ui.app` or running a parser/import check rather than starting the event loop.

## Testing and Linting

Common checks:

```bash
pytest tests/
pytest tests/test_graphIO.py -q
pytest tests/test_nodes.py::TestOutputNode -q
flake8 . --max-line-length=127
```

Do not use full photogrammetry pipelines as routine framework verification unless the task explicitly needs external AliceVision behavior and the required binaries/data are available.
