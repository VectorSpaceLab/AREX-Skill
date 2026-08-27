# Pipeline workflows

Use this file when the task is to assemble, update, or inspect a SageMaker
pipeline. Build the upstream step arguments in the training, serving, or core
resource sub-skill, then wire them together here.

## Import map

```python
from sagemaker.mlops.workflow import (
    Pipeline,
    PipelineExecution,
    PipelineGraph,
    TrainingStep,
    ProcessingStep,
    TransformStep,
    TuningStep,
    ModelStep,
    ConditionStep,
    CacheConfig,
    RetryPolicy,
    StepRetryPolicy,
    SageMakerJobStepRetryPolicy,
    ParallelismConfiguration,
    SelectiveExecutionConfig,
    PipelineExperimentConfig,
    PipelineDefinitionConfig,
    PipelineSchedule,
    Trigger,
    CheckJobConfig,
)
from sagemaker.core.workflow.pipeline_context import PipelineSession
from sagemaker.core.workflow import ParameterString, ParameterInteger, JsonGet, Join, PropertyFile
```

## Assembly pattern

1. Build the upstream job config in another sub-skill.
2. Capture the returned `step_args` or properties.
3. Create the pipeline parameters and step objects.
4. Add retry, caching, and selective-execution settings if needed.
5. Create or update the pipeline.
6. Start an execution and inspect it through `PipelineExecution`.

## Core lifecycle

- `Pipeline.create(...)`
- `Pipeline.update(...)`
- `Pipeline.upsert(...)`
- `Pipeline.start(...)`
- `PipelineExecution(...)` for post-start inspection
- `PipelineGraph.from_pipeline(pipeline)` for graph inspection

## Local execution

Use `PipelineSession` when a local or pipeline-aware session is needed.
Local pipeline execution is useful for inspection, but it does not fully replace
cloud execution. `ParallelismConfiguration` is not supported in local mode.

## Service boundaries

- Do not put a step in both the main pipeline step list and a condition branch.
- Use `JsonGet` and `PropertyFile` for outputs that need to flow into later
  steps.
- Use `Trigger` / `PipelineSchedule` for scheduled or event-driven execution.
- Use `CheckJobConfig` for quality or Clarify check jobs.

## Example sketch

```python
from sagemaker.mlops.workflow import Pipeline, TrainingStep, CacheConfig
from sagemaker.core.workflow.pipeline_context import PipelineSession

pipeline = Pipeline(
    name="<pipeline-name>",
    steps=[],
    sagemaker_session=PipelineSession(),
)
```

## Handoff rules

- For `step_args`, go back to the training, serving, or core-resource sub-skill.
- For feature store or registry wiring, use the sibling reference file.
- For lineage and governance, use the sibling reference file.
