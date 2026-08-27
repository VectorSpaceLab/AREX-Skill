# QGIS Plugin and MCP Integration Surface

This reference covers the integration layer only:
QGIS plugin panels, the managed dependency installer, Pixi/uv decisions, diagnostics, and the GeoAI MCP server configuration surface.
Underlying model workflows belong to sibling sub-skills.

## QGIS plugin route

The QGIS plugin exposes dockable panels for:

- Tree Segmentation
- Water Segmentation
- Moondream VLM
- Segment Anything
- Semantic Segmentation
- Instance Segmentation
- GPU memory cleanup
- Update checking
- Diagnostics report generation

### Installation choices

- Use the QGIS Plugin Manager for the simplest desktop install.
- Use the plugin dependency installer when you want the managed environment to create a private venv and install the required AI stack automatically.
- Use Pixi when you need explicit control over Python, QGIS, PyTorch, or CUDA versions.
- Treat the source-tree profile-copy and packaging helpers as maintainer-only references; they are not part of the runtime workflow in this sub-skill.

### Managed dependency installer

The installer creates and reuses a managed cache under the GeoAI cache directory.
It resolves the QGIS process Python mismatch by running model code in the managed venv, not in the embedded QGIS interpreter.

Key behaviors:

- Downloads a standalone Python runtime when needed.
- Downloads uv when available and falls back to pip when not.
- Creates an isolated venv in the managed cache.
- Installs the base GeoAI plugin stack, including torch, torchvision, geoai-py, segment-geospatial, sam3, deepforest, omniwatermask, and transformers.
- On Windows, adds triton-windows when required so SAM3 imports can resolve.
- Treats sam3 as optional on macOS when the platform cannot satisfy its native stack.
- Detects NVIDIA GPUs and chooses a CUDA wheel index when possible.
- Falls back to CPU when the driver is too old or no usable GPU is found.

Managed cache variables:

- `GEOAI_CACHE_DIR`
- `GEOAI_VENV_DIR`

If neither is set, the plugin uses a home-directory cache under `~/.qgis_geoai/`.

### Pixi and CUDA decisions

Prefer Pixi when the dependency stack is sensitive to CUDA or QGIS version pinning.
The plugin docs use QGIS 3.44.* for a reason: older 3.42.2 Windows builds had a project-save zip regression.
If users hit a `.qgz` save failure, update QGIS or save as `.qgs` until the stack is corrected.

For GPU paths:

- NVIDIA CUDA is preferred on Windows and Linux when the driver supports the selected wheel index.
- Apple Silicon can use MPS at runtime for supported workers.
- CPU remains the safe fallback.

### Proxy and download handling

The installer and uv helper respect QGIS proxy settings.
If corporate networking blocks downloads, check the QGIS proxy configuration before retrying.
Do not change the user environment from this skill; use diagnostics first.

### Diagnostics

The diagnostics report is the first thing to ask for when a user reports a QGIS plugin issue.
It captures:

- QGIS version
- Python version and executable
- Managed environment paths
- GPU detection
- Package import state
- CUDA or MPS availability

The report is Markdown and is safe to copy into an issue tracker.

## MCP server route

The GeoAI MCP server is a local stdio server for agents such as Claude Desktop.
It exposes sandboxed geospatial tools through a JSON config and environment variables.

### Server launch surfaces

The server can be started as either:

- the installed console script `geoai-mcp-server`
- the module entry point `geoai_mcp_server.server`

It logs to stderr or to a configured file and should not write operational output to stdout.

### Core environment variables

- `GEOAI_INPUT_DIR` - sandbox root for readable inputs
- `GEOAI_OUTPUT_DIR` - sandbox root for writable outputs
- `GEOAI_TIMEOUT` - timeout in seconds
- `GEOAI_MAX_MEMORY_GB` - soft memory budget
- `GEOAI_DEVICE` - `auto`, `cuda`, `mps`, or `cpu`
- `GEOAI_LOG_LEVEL` - logging level
- `GEOAI_LOG_FILE` - optional file log path
- `GEOAI_MODEL_CACHE_SIZE` - cached model count

### Sandboxing rules

The server validates file access inside the configured input and output directories.
It rejects path traversal attempts and glob patterns that escape the sandbox.
Use sandboxed directories that are dedicated to the MCP server and avoid sharing them with unrelated data.

### Claude Desktop validation

Before starting the server from Claude Desktop or a similar client:

1. Confirm the command points to the installed server entry point.
2. Confirm the working directory is the server project or install location.
3. Confirm the input and output sandbox paths are absolute and writable.
4. Confirm the timeout and device settings match the user machine.
5. Validate the config with [mcp_config_check.py](../scripts/mcp_config_check.py).

## Routing boundaries

Route the following elsewhere:

- segmentation and detection inference work to `detection-segmentation-inference`
- training and dataset preparation to `training-and-finetuning`
- download, tile, and raster/vector prep work to `geospatial-data-pipelines`
- foundation model registry and VLM tasks to `foundation-models-embeddings-vlms`

This sub-skill only owns the integration layer, config validation, and troubleshooting.
