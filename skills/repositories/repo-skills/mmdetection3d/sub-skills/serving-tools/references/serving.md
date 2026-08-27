# Serving packaging

## Scope

This sub-skill covers the artifact and runtime assumptions around serving-time packaging and release helpers:

- TorchServe archive packaging,
- handler expectations,
- checkpoint publishing and conversion,
- Conv+BN fusion before release,
- and the safe preflight of packaging inputs.

## Packaging inputs

A complete packaging request should provide:

- config file,
- checkpoint file,
- handler file,
- model name,
- export folder.

Use the bundled checker before packaging:

```bash
python scripts/check_serving_artifacts.py CONFIG CHECKPOINT \
  --handler HANDLER \
  --model-name MODEL_NAME \
  --output-folder OUTPUT_FOLDER
```

The checker only validates the requested paths and names. It never packages, starts a server, builds Docker images, or downloads anything.

## TorchServe packaging facts

- Packaging creates a `.mar` archive from a config/checkpoint pair.
- The packager writes a temporary config copy before archiving.
- The archive uses a Python runtime and the bundled handler.
- Packaging requires the `torch-model-archiver` / `model_archiver` dependency.
- Keep the config/checkpoint pair local for reproducibility.
- The export folder should be writable. The packager can create the directory when needed.

## Handler assumptions

- The bundled handler is a LiDAR point-cloud handler.
- It expects float32 point bytes, reshapes by `load_dim=4`, and keeps dims `[0, 1, 2, 3]`.
- It interprets the input as `coord_type='LIDAR'`.
- It applies a score threshold of `0.5` during postprocess.
- Its docstring says the handler is only validated for SECOND-style models.
- Requests may arrive as raw bytes or base64 strings.

## Publishing and conversion helpers

| Helper family | Use when | Notes |
| --- | --- | --- |
| Checkpoint publishing | You want a release-ready checkpoint copy. | Removes optimizer state and appends a hash suffix to the filename. |
| Conv+BN fusion | You want a frozen model checkpoint with paired Conv/BN layers fused. | Only use when the layer order matches the fusion rule. |
| Legacy H3DNet / VoteNet conversion | You need to upgrade an old checkpoint layout. | One-off migration scripts with strict state-dict loading. |
| RegNet conversion | You need to remap external RegNet backbone weights. | Backbone conversion only; not a serving runtime helper. |

## Deployment caveats

- This bundle only prepares artifacts; it does not build or run containers.
- If the user needs a different deployment backend or runtime handler, route to a separate deployment workflow.
- Do not promise support beyond the validated handler and model family.
