# Lineage, monitoring, and governance

Use this file when the task is about provenance, auditability, quality gates, or
workflow governance.

## Lineage surface

Prefer `sagemaker.core.lineage` for new code:

```python
from sagemaker.core.lineage import Context, Action, Artifact, Association
```

### Lineage rules

- create the logical context first
- record the action that produced the artifact
- associate the entities explicitly
- delete associations before deleting the linked entities

## Monitoring and checks

Governance-oriented pipeline steps include:

- `QualityCheckStep`
- `ClarifyCheckStep`
- `MonitorBatchTransformStep`
- `CheckJobConfig`

Use them when the pipeline must enforce data quality, model quality, bias, or
explainability gates before promotion.

## Operational controls

- `Trigger` and `PipelineSchedule` support event-driven or scheduled workflows.
- `RetryPolicy`, `StepRetryPolicy`, and `SageMakerJobStepRetryPolicy` help with
  recovery.
- `SelectiveExecutionConfig` can target a subset of steps when re-running a
  pipeline.

## Good practice

- Keep lineage creation close to the steps that produce the tracked artifacts.
- Use the pipeline execution object for inspection after start.
- Keep governance logic in the pipeline layer; keep the job implementation in
  the training, serving, or processing sub-skill.
