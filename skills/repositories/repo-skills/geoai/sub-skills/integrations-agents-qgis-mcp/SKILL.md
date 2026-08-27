---
name: integrations-agents-qgis-mcp
description: "Route GeoAI QGIS plugin, MCP server, and optional Strands agent
  integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GeoAI Integrations, Agents, QGIS, and MCP

Use this sub-skill when the user is configuring, validating, or troubleshooting GeoAI integration surfaces rather than the underlying model or geospatial algorithm.

## Route here for

- QGIS plugin setup: plugin panels, dependency installer, managed venv/cache location, Pixi/uv installation decisions, GPU/MPS choices, and diagnostics reports. Start with [QGIS plugin and MCP workflows](references/qgis-plugin-and-mcp.md).
- GeoAI MCP server setup: Claude Desktop or other MCP client configuration, server environment variables, sandboxed input/output directories, stdio logging, and safe config validation. Start with [QGIS plugin and MCP workflows](references/qgis-plugin-and-mcp.md).
- `geoai.agents` surfaces: optional Strands extras, model/provider constructors, `GeoAgent`, `STACAgent`, `CatalogAgent`, and map/catalog/STAC tool routing. Use [API reference](references/api-reference.md).
- Failures involving QGIS Python/PyQt process mismatch, managed venv packages, CUDA/MPS install choices, MCP sandbox paths, provider keys, or missing Strands extras. Use [troubleshooting](references/troubleshooting.md).

## Delegate elsewhere

- Raster/vector I/O, STAC/NAIP/Overture data acquisition, and pipeline configs: `geospatial-data-pipelines`.
- Segmentation, detection, RF-DETR, SAM, water/cloud/super-resolution, ONNX, and model inference: `detection-segmentation-inference`.
- Dataset preparation, training, finetuning, metrics, and Hub pushes: `training-and-finetuning`.
- Foundation model registries, embeddings, DINOv3/Prithvi/UniverSat/TESSERA, Moondream, and vLLM model workflows: `foundation-models-embeddings-vlms`.

## Operating rules

1. Keep integration work safe by default: do not launch model downloads, long inference, training, QGIS profile mutation, external data downloads, or credentialed release/upload operations unless the user explicitly requests that downstream action and the appropriate sibling skill owns it.
2. For QGIS plugin dependency failures, prefer diagnostics and static probes before reinstalling anything. Use [qgis_dependency_probe.py](scripts/qgis_dependency_probe.py) for a no-install package-plan check.
3. For MCP client setup, validate JSON and sandbox paths before starting the server. Use [mcp_config_check.py](scripts/mcp_config_check.py) to inspect Claude Desktop style configs or current environment variables.
4. Treat provider credentials as user-managed secrets. Check variable names and process inheritance, but never print API key values or ask for keys in chat.
5. Do not handle credentialed QGIS plugin upload/release workflows in this sub-skill; those are maintainer release side effects and are intentionally excluded.

## Quick checks

From this sub-skill directory:

```bash
python scripts/qgis_dependency_probe.py --help
python scripts/mcp_config_check.py --help
```

Both scripts are read-only diagnostics. They do not install packages, start QGIS, start an MCP server, download models/data, train models, write credentials, or modify user directories.
