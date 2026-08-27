# Optimization and training

AdalFlow optimization turns task-pipeline text into trainable `Parameter` objects, scores predictions with evaluators, converts scores into textual gradients, and lets optimizers propose new prompts or demonstrations. Treat this as an explicit training workflow, not a default inference path.

## Core object map

| Object | Role | Verified API facts |
|---|---|---|
| `Parameter` | Stores trainable or non-trainable values and graph metadata. | `Parameter(data=..., requires_opt=True, role_desc="", param_type=ParameterType.NONE, name=None, eval_input=None, instruction_to_optimizer=None, instruction_to_backward_engine=None, score=None, ...)` |
| `ParameterType` | Tells optimizers what a parameter means. | `PROMPT`, `DEMOS`, `INPUT`, `OUTPUT`, `HYPERPARAM`, `GENERATOR_OUTPUT`, `RETRIEVER_OUTPUT`, `LOSS_OUTPUT`, `SUM_OUTPUT`, `NONE` |
| `GradComponent` | Component with training-mode `forward`, graph tracing, and `backward` support. | `GradComponent(desc, name=None, backward_engine=None, model_client=None, model_kwargs=None)` |
| `EvalFnToTextLoss` | Wraps an evaluator into a loss `Parameter` that can backpropagate textual feedback. | `EvalFnToTextLoss(eval_fn, eval_fn_desc, backward_engine=None, model_client=None, model_kwargs=None)` |
| `LLMAsTextLoss` | Uses a model-backed generator as an evaluation loss. | `LLMAsTextLoss(prompt_kwargs, model_client, model_kwargs)` |
| `BootstrapFewShot` | Samples raw and teacher-augmented demos for `ParameterType.DEMOS`. | `BootstrapFewShot(params, raw_shots=None, bootstrap_shots=None, dataset=None, weighted=True, exclude_input_fields_from_bootstrap_demos=False)` |
| `TGDOptimizer` | Textual-gradient optimizer for `ParameterType.PROMPT`. | Configured directly or by `AdalComponent.configure_text_optimizer_helper`; requires model client/kwargs. |
| `AdalComponent` | User subclass that defines task/eval/loss/optimizer hooks for `Trainer`. | `AdalComponent(task, eval_fn=None, loss_eval_fn=None, loss_fn=None, backward_engine=None, backward_engine_model_config=None, teacher_model_config=None, text_optimizer_model_config=None, ...)` |
| `Trainer` | Diagnosis and optimization loop. | `Trainer(adaltask, optimization_order="sequential", strategy="constrained", max_steps=1000, train_batch_size=4, num_workers=4, ckpt_path=None, ...)` |
| `optimize_anything` | GEPA-style local search over arbitrary text candidates. | `optimize_anything(seed_candidate, evaluator, objective, config)` where evaluator returns float/int or dict with `score`. |

## `Parameter` and `ParameterType`

Use `Parameter` for values that must appear in prompts, participate in optimization, or carry `eval_input` into loss functions.

Common choices:

- `ParameterType.PROMPT`: task instructions, formatting instructions, or other prompt text optimized by `TGDOptimizer`.
- `ParameterType.DEMOS`: few-shot examples optimized by `BootstrapFewShot`.
- `ParameterType.INPUT`: non-trainable task input if you need graph context.
- `ParameterType.HYPERPARAM`: non-trainable prompt/config values.
- `ParameterType.NONE`: generic parameter when optimizer routing is not needed.

Example prompt parameters:

```python
system_prompt = adal.Parameter(
    data="Classify the question into one of ABBR, ENTY, DESC, HUM, LOC, NUM.",
    role_desc="classification instruction",
    param_type=adal.ParameterType.PROMPT,
    instruction_to_optimizer="Preserve the six-label output space.",
)

few_shot_demos = adal.Parameter(
    data=None,
    role_desc="few-shot demonstrations",
    param_type=adal.ParameterType.DEMOS,
)
```

Parameter hygiene:

- Use descriptive `role_desc` and `name`; optimizer prompts depend on them.
- Set `requires_opt=False` for ground truth and constants.
- Set `eval_input` to the exact scalar/string the evaluator expects.
- Keep trainable prompt data as text or YAML-like demo strings; avoid embedding private paths or secrets in optimizer-visible text.

## `GradComponent` and loss wrappers

`GradComponent` extends `Component` with a training-mode `forward` path that returns a `Parameter` and tracks predecessors. Model generators are adapted into this pattern, so a task can call normal inference in eval mode and return traceable parameters in train mode.

For deterministic evaluator loss, use `EvalFnToTextLoss`:

```python
eval_fn = AnswerMatchAcc(type="exact_match").compute_single_item
loss_fn = adal.EvalFnToTextLoss(
    eval_fn=eval_fn,
    eval_fn_desc="exact_match: 1 when normalized prediction equals ground truth, else 0",
)
```

In `prepare_loss`, all `kwargs` passed to `EvalFnToTextLoss.forward` must be `Parameter` objects. The wrapped evaluator receives each parameter's `eval_input` values, not necessarily its full textual prompt data.

`LLMAsTextLoss` is model-backed. Use it only when the user has accepted provider setup, latency, and judge-risk constraints. For many QA/classification workflows, `EvalFnToTextLoss` with `AnswerMatchAcc` is cheaper and easier to debug.

## `AdalComponent` contract

Subclass `AdalComponent` whenever you want `Trainer` to diagnose or optimize a task. Implement at least:

```python
class MyTaskAdal(adal.AdalComponent):
    def __init__(self, task, model_configs=None):
        eval_fn = AnswerMatchAcc(type="exact_match").compute_single_item
        loss_fn = adal.EvalFnToTextLoss(
            eval_fn=eval_fn,
            eval_fn_desc="exact normalized answer match",
        )
        super().__init__(
            task=task,
            eval_fn=eval_fn,
            loss_fn=loss_fn,
            backward_engine_model_config=model_configs.get("backward") if model_configs else None,
            text_optimizer_model_config=model_configs.get("text_optimizer") if model_configs else None,
            teacher_model_config=model_configs.get("teacher") if model_configs else None,
        )

    def prepare_task(self, sample):
        return self.task.bicall, {"question": sample.question, "id": sample.id}

    def prepare_eval(self, sample, y_pred):
        y_value = -1
        if y_pred is not None and getattr(y_pred, "data", None) is not None:
            y_value = y_pred.data
        return self.eval_fn, {"y": y_value, "y_gt": sample.answer}

    def prepare_loss(self, sample, y_pred):
        y_pred.eval_input = y_pred.full_response.data
        y_gt = adal.Parameter(
            name="y_gt",
            data=sample.answer,
            eval_input=sample.answer,
            requires_opt=False,
        )
        return self.loss_fn, {"kwargs": {"y": y_pred, "y_gt": y_gt}, "id": sample.id, "gt": sample.answer}
```

Contract details:

- `prepare_task(sample)` returns `(callable, kwargs)` for exactly one sample.
- In eval mode, the task callable must return an inference output, not a `Parameter`.
- In train mode, the task callable must return a `Parameter` so gradients can trace through the graph.
- `prepare_eval(sample, y_pred)` returns `(eval_fn, kwargs)` and should be robust to parser failures by assigning a sentinel value.
- `prepare_loss(sample, y_pred)` returns `(loss_fn, kwargs)` and should wrap ground truth as `requires_opt=False`.
- For diagnosis output alignment, pass a stable sample `id` through task calls when the task output supports it.

## Few-shot and text-gradient optimization

`AdalComponent.configure_demo_optimizer_helper` finds task parameters with `ParameterType.DEMOS` and configures `BootstrapFewShot`. `Trainer` supplies the train dataset and shot counts.

`AdalComponent.configure_text_optimizer_helper` finds task parameters with `ParameterType.PROMPT` and configures `TGDOptimizer`. This requires `text_optimizer_model_config` containing a model client and model kwargs.

Typical `Trainer` setup:

```python
trainer = adal.Trainer(
    adaltask=adal_component,
    optimization_order="sequential",  # or "mix"
    strategy="constrained",           # or "random"
    max_steps=12,
    train_batch_size=4,
    num_workers=4,
    raw_shots=0,
    bootstrap_shots=1,
    weighted_sampling=True,
    exclude_input_fields_from_bootstrap_demos=True,
)

ckpt_file, result = trainer.fit(
    train_dataset=train_dataset,
    val_dataset=val_dataset,
    test_dataset=test_dataset,
    debug=False,
)
```

Scaling guidance:

- Start with `max_steps=1`, `train_batch_size=1`, `num_workers=1`, and a tiny dataset slice.
- Increase `num_workers` only after provider rate limits and task thread-safety are known.
- Use `optimization_order="sequential"` to optimize text first and demos second; use `"mix"` only when the user wants joint proposals.
- Keep `max_proposals_per_step` small for constrained search.
- Use `disable_backward=True` or `disable_backward_gradients=True` only for debugging pathways where no text-gradient feedback should be generated.

## `Trainer.diagnose`

`diagnose(dataset, split="train", resume_from_ckpt=None)` evaluates a dataset, saves callback logs, sorts samples by score, and identifies low-scoring responses. Use it before full training when the model already runs but errors need inspection.

Requirements:

- Dataset items should have an `id` attribute for stable alignment.
- `prepare_task` should pass the id through to task outputs where applicable.
- `prepare_eval` must work in inference mode and return scalar scores.
- Checkpoint/log paths should be user-approved writable locations if defaults are not desired.

Cheap diagnosis run:

```python
trainer = adal.Trainer(adaltask=adal_component, num_workers=1)
trainer.diagnose(dataset=small_train_slice, split="train")
```

## `Trainer.fit`

`fit` requires either `train_loader` or `train_dataset`, and requires `val_dataset`. A missing validation set is a hard error. `test_dataset` is optional but useful for reporting.

Important fit arguments:

- `resume_from_ckpt`: restore parameters from a previous checkpoint result.
- `debug=True`: smaller deterministic/debug path; combine with small data and `num_workers=1`.
- `save_traces=True`: useful but can produce large artifacts; route tracing/logging questions to the tracing sub-skill.
- `backward_pass_setup`: advanced text-gradient setup when the user already has a provider plan.

Checkpoint behavior:

- `Trainer` can save checkpoint files and restore prompt values via `resume_params_from_ckpt`/`resume_from_ckpt`.
- Keep checkpoint paths outside runtime skill files; ask the user for a project-appropriate path if persistence matters.
- If a checkpoint fails to load, verify it is a serialized `TrainerResult` with step prompt data.

## `optimize_anything`

`optimize_anything` is a GEPA-style API for optimizing any text artifact with a bounded evaluator. It does not need a model provider unless the evaluator itself calls one.

```python
from adalflow.optim import optimize_anything, GEPAConfig, EngineConfig, log


def evaluator(candidate: str):
    score = 1.0 if "must" in candidate.lower() else 0.2
    log("Reward instructions that include a clear must-clause.")
    return {"score": score, "token_cost": len(candidate.split())}

config = GEPAConfig(
    engine=EngineConfig(max_metric_calls=8, random_seed=0),
    population_size=4,
    elite_size=2,
    stop_score=1.0,
)
result = optimize_anything(
    seed_candidate="Answer concisely.",
    evaluator=evaluator,
    objective="Improve instruction compliance while keeping the prompt short.",
    config=config,
)
print(result.best_candidate, result.best_score)
```

Controls:

- `EngineConfig.max_metric_calls` is the primary hard budget.
- `GEPAConfig.population_size`, `elite_size`, `mutation_rate`, `crossover_rate`, and `stop_score` control local search.
- Evaluators may return `float`, `int`, or a dict containing `score` plus optional `token_cost` and `latency_ms`.
- Treat `max_parallel` as configuration metadata unless the installed runtime explicitly uses it for parallel execution.
