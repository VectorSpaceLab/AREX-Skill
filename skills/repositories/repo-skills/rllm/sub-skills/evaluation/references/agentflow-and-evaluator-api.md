# AgentFlow and Evaluator API Reference

## Import map

```python
from rllm import rollout, evaluator, Task, Episode, Trajectory, Step
from rllm.types import AgentConfig, AgentFlow, Evaluator, run_agent_flow
from rllm.eval.types import EvalOutput, Signal
```

Confirmed details for this source revision:

- `rollout` and `evaluator` are top-level exports from `rllm`.
- `AgentConfig` is in `rllm.types`.
- `EvalOutput` and `Signal` are in `rllm.eval.types`.
- Legacy trajectory types are re-exported from `rllm`, but their canonical home is `rllm.types`.

## Decorator signatures

```python
rollout(fn=None, *, name="solver", register=None)
evaluator(fn=None, *, register=None)
```

`@rollout` wraps a callable as an `AgentFlowFn`. Its `run(task, config)` method passes a `Task`-like object and an `AgentConfig(base_url, model, session_uid, metadata, is_validation, sampling_params)` to the function.

`@evaluator` wraps a callable as an `EvaluatorFn`. It accepts evaluators that return:

- `EvalOutput(reward=..., is_correct=..., signals=[...], metadata={...})`;
- a `float` reward;
- a `bool` correctness value;
- a `(float, bool)` pair.

Unsupported evaluator return types raise a `TypeError`.

## AgentFlow return contract

`AgentFlow.run` or `AgentFlow.arun` may return:

- `Episode`: passed through, with task metadata filled if absent;
- `Trajectory`: wrapped into a one-trajectory `Episode`;
- `None`: converted to an empty trajectory so gateway traces can enrich it later.

Returning raw strings, dicts, or arbitrary objects is invalid. Put messages/actions into `Step`, `Trajectory`, and `Episode` objects, or return `None` when the framework/gateway is expected to supply trace steps.

## Workflow classes

Current import locations:

```python
from rllm.workflows.workflow import Workflow
from rllm.workflows.simple_workflow import SimpleWorkflow
from rllm.workflows.multi_turn_workflow import MultiTurnWorkflow
from rllm.workflows.cumulative_workflow import CumulativeWorkflow
```

`SimpleWorkflow` is not exported directly from `rllm.workflows` in this revision. Use the module import above.

## Built-in loading

Evaluation CLI and training paths use loaders with this broad lookup behavior:

- user registry entries under rLLM home;
- `module:object` or import-path references;
- built-in catalogs;
- package entry points.

When debugging resolution, first determine whether the user provided a registry name, an import path, or a built-in catalog name.
