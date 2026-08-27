# Installation and Environment

## Purpose

Read this before using the GeoAI repo skill in a new environment or when a task needs extra dependency coverage. It summarizes the public package identity, install paths, and the main optional extras so you can choose the smallest useful setup.

## Package facts

- Distribution: `geoai-py`
- Import name: `geoai`
- Console entry point: `geoai`
- Python support: Python 3.12 or newer
- Base runtime: the published package installs the broad geospatial and ML stack from `requirements.txt`

## Install the base package

```bash
pip install geoai-py
```

When working from a local checkout, editable install is also supported:

```bash
pip install -e .
```

## Minimal smoke checks

After install, confirm the package is visible and the CLI is wired up:

```bash
python -c "import geoai; print(geoai.__version__)"
python -m geoai.cli --help
```

If you need a fuller read-only check, use the bundled helper:

```bash
python scripts/check_geoai_env.py --check-cli
```

## Optional extras

Install an extra only when the task actually needs that workflow.

| Extra | Typical use | Owning sub-skill |
| --- | --- | --- |
| `agents` | Strands model/provider and agent tools | `integrations-agents-qgis-mcp` |
| `building` | Building-specific model helpers | `training-and-finetuning` or `detection-segmentation-inference` |
| `networks` | Road-network simplification helpers | `geospatial-data-pipelines` |
| `onnx` | ONNX export and ONNXRuntime inference | `detection-segmentation-inference` |
| `osd` | Optically shallow deep water classification | `detection-segmentation-inference` |
| `rfdetr` | RF-DETR detection and segmentation | `detection-segmentation-inference` |
| `sr` | Super-resolution workflow helpers | `detection-segmentation-inference` |
| `terratorch` | TerraTorch-backed foundation-model loading | `foundation-models-embeddings-vlms` |
| `vllm` | Local vLLM-backed geospatial VLM workflows | `foundation-models-embeddings-vlms` |

The package also exposes `extra`, which aggregates several convenience dependencies for broader geospatial workflows. Use it only when you truly need that wider surface.

## GPU and backend notes

- GeoAI can use CUDA when the installed PyTorch build and host driver are compatible.
- A successful CPU import does not prove GPU readiness.
- Use the bundled environment check script to confirm CUDA availability before a model-heavy workflow.
- For QGIS or MCP tasks, the integration sub-skill owns the environment-specific guidance.

## When to read this again

- The package version changes.
- The install requirements or optional extras change.
- A user asks for a new environment, a fresh editable install, or a backend-capability check.
