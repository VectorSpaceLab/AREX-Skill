# Evaluation and AI Registry

Use this file when the task is about evaluating customized models or managing
AI Registry datasets and evaluators.

## Evaluation surface

The evaluation module exports:

- `BenchMarkEvaluator`
- `CustomScorerEvaluator`
- `LLMAsJudgeEvaluator`
- `InspectAIEvaluator`
- `MultiTurnRLEvaluator`
- `EvaluationPipelineExecution`
- benchmark helper functions such as `get_benchmarks()` and
  `get_benchmark_properties()`

## AI Registry surface

The registry objects live in `sagemaker.ai_registry`:

```python
from sagemaker.ai_registry.dataset import DataSet
from sagemaker.ai_registry.evaluator import Evaluator
```

### `DataSet`

Use `DataSet` when the training or evaluation data should be registered as a
first-class AI Registry asset.

Helpful methods:

- `DataSet.get(...)`
- `DataSet.create(...)`
- `refresh()`

### `Evaluator`

Use `Evaluator` when the reward or judging logic should be registered as a
first-class AI Registry asset.

Helpful methods:

- `Evaluator.get(...)`
- `Evaluator.create(...)`
- `refresh()`

## Monitoring helpers

The package also exposes monitoring helpers for post-submission inspection:

- `show_metrics()`
- `stream_logs()`
- `plot_training_metrics()`
- `AgentRFTJob.get_training_metrics()`
- `AgentRFTJob.stream_logs()`
- `AgentRFTJob.get_mlflow_url()`

## Dry-run validation

The evaluation APIs support `dry_run=True` to validate the configuration
without launching a job. Use that before any live AWS submission.

## Usage pattern

1. Register or refresh datasets and evaluators when you need reusable assets.
2. Build the evaluator or benchmark that matches the task.
3. Run `dry_run=True` first.
4. Inspect logs and metrics after the job starts.

## Hand off when needed

- For recipe precedence, data mixing, and notifications, use the sibling
  reference file.
- For ordinary training, return to the training sub-skill.
- For deployment, hand the task to the serving sub-skill.
