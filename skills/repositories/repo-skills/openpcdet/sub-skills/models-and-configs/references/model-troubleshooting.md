# Model and Config Troubleshooting

## Config override errors

- `NotFoundKey`: the override path does not exist in the loaded config. Inspect with the config summarizer and use exact nested keys.
- Type mismatch assertion: the override string did not parse to the original value type. Lists must preserve element types; numeric strings must parse as numbers when the original is numeric.
- `_BASE_CONFIG_` surprises: base dataset config values are merged before the model config's local keys; inspect the merged config, not only the top-level YAML.

## Registry errors

- `KeyError` in detector registry: `MODEL.NAME` is not imported and listed in detector `__all__`.
- `KeyError` in dataset registry: `DATA_CONFIG.DATASET` is not imported and listed in dataset `__all__`.
- Missing module component: VFE/backbone/head `NAME` fields must match the relevant submodule registry, not just the detector registry.

## Checkpoint/config mismatch

Symptoms:

- Missing/unexpected checkpoint keys.
- Tensor shape mismatches in heads.
- Evaluation metrics nonsensical despite no exception.

Checks:

1. Same detector `MODEL.NAME`.
2. Same `CLASS_NAMES` count/order.
3. Same point feature encoding and point range.
4. Same voxel size / grid size dependent modules.
5. Same image branch / sweeps / temporal settings for fusion or multi-frame models.

## Selecting a safer baseline

When the user needs a quick smoke or a custom-data starting point, choose simpler LiDAR-only configs before image-fusion or temporal configs:

- PointPillar or SECOND-style configs for basic LiDAR pipelines.
- CustomDataset configs for custom point files/classes.
- Avoid BEVFusion/CaDDN unless image/camera inputs are present.
- Avoid MPPNet/temporal configs unless sequence data is prepared.
