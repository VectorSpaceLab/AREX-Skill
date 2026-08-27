# Processing, feature store, and registry

Use this file for the pipeline pieces that sit around data processing, feature
store orchestration, and model registry.

## Imports and surfaces

```python
from sagemaker.mlops.workflow import ProcessingStep, TrainingStep, TransformStep, ModelStep
from sagemaker.mlops.workflow import QualityCheckStep, ClarifyCheckStep
from sagemaker.mlops.feature_store import (
    FeatureGroup,
    FeatureGroupManager,
    LakeFormationConfig,
    IcebergProperties,
    DatasetBuilder,
    ingest_dataframe,
    load_feature_definitions_from_dataframe,
)
```

## Processing step patterns

- Build `step_args` with the core-resource or training sub-skill.
- Use `ProcessingStep` property files and `JsonGet` when later steps need
  output values.
- Keep the processing logic outside the pipeline file; the pipeline should only
  orchestrate.

## Feature store patterns

- Use `FeatureGroup` for ordinary feature-group CRUD.
- Use `FeatureGroupManager` when Lake Formation or Iceberg governance matters.
- Use `DatasetBuilder` when you need a structured dataset assembled from one or
  more feature groups.
- Use `load_feature_definitions_from_dataframe(...)` when you are deriving the
  schema from a dataframe.
- Use `ingest_dataframe(...)` for ingestion helpers.

## Registry patterns

`ModelStep` is the pipeline bridge to model packaging and registry flows.
Use it when the pipeline should register a trained model, promote an existing
model package, or continue to deployment gating.

## Quality and Clarify checks

`QualityCheckStep` and `ClarifyCheckStep` belong here when the pipeline needs
quality gates before promotion.
Use `CheckJobConfig` from the workflow package when you need to shape the check
job resources.

## Recommended handoff order

1. Build preprocessing in the processing or core-resource sub-skill.
2. Build training step args in the training or customization sub-skill.
3. Add feature store or registry orchestration here.
4. Wire deployment in the serving or pipeline step flow as needed.
