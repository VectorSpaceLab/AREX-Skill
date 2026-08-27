---
name: "data-and-models"
description: "Data modules, datasets, dataclasses, model registry, constructors,
  feature extraction, and custom data-layout guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data and Models

Use this sub-skill for anomalib questions about choosing, configuring, and debugging data or model entry points.

## Use this when the user asks about

- Image datamodules: `MVTecAD`, `Folder`, `Tabular`, `PredictDataset`
- Video datamodules: `Avenue`, `ShanghaiTech`, `UCSDped`
- Depth datamodules: `MVTec3D`, `Folder3D`, `ADAM3D`
- Dataclasses and batch shapes: `ImageItem`, `VideoItem`, `DepthItem`, and their batch types
- Model registry and lookup: `get_model`, `list_models`, `get_datamodule`
- Core model constructors: `Padim`, `Patchcore`, `EfficientAd`, `AiVad`, `Fuvas`
- Backbone / layer selection and feature extraction with `TimmFeatureExtractor`
- Custom folder, tabular, video, or depth data layouts
- Unknown model names, registry lookup errors, or feature-layer mismatches

## Do not use this when the user asks about

- Engine fit / validate / test / predict execution
- Export, deployment, or inference packaging
- Pipeline orchestration or benchmark automation
- CLI install mechanics
- Studio application content

## Fast routing

- Data layout, dataclasses, and config shapes: [references/data-and-models.md](references/data-and-models.md)
- Model selection, constructors, and feature extraction: [references/model-overview.md](references/model-overview.md)
- Failure modes, optional dependencies, and lookup errors: [references/troubleshooting.md](references/troubleshooting.md)
- Lightweight discovery / validation helper: [scripts/inspect_data_models.py](scripts/inspect_data_models.py)

## Primary source surfaces

- `src/anomalib/data/**`
- `src/anomalib/models/**`
- `docs/source/markdown/guides/how_to/data/**`
- `docs/source/markdown/guides/how_to/models/**`
- `docs/source/markdown/guides/reference/data/index.md`
- `docs/source/markdown/guides/reference/models/index.md`
- `examples/api/02_data/**`
- `examples/api/03_models/**`
- `tests/unit/data/**`
- `tests/unit/models/**`
- `tests/integration/model/test_models.py`

## Helpful mental model

1. Choose the data family first: image, video, depth, custom folder, or tabular.
2. Confirm the datamodule layout and split mode before choosing a model.
3. For backbone-based image models, confirm the backbone / layer names before instantiating.
4. For video models, confirm clip length and target frame semantics.
5. If the user needs a quick sanity check, use the bundled inspection script instead of guessing.

## Discovery and validation script

The bundled script can:

- list key datamodule and model constructors
- print the current `list_models()` registry
- validate custom folder layouts by calling anomalib's own folder parser
- validate custom tabular layouts with anomalib-style rules

Example invocations:

```bash
python scripts/inspect_data_models.py list
python scripts/inspect_data_models.py check-folder --help
python scripts/inspect_data_models.py check-tabular --help
```

## Notes

- Prefer the exact public constructors and helpers documented in the bundled references.
- Keep training, export, and pipeline questions routed to the other sub-skills.
- Use the bundled references for exact argument defaults, path rules, and dependency caveats.
