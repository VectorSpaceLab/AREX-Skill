# Python API for Evaluation Runs

Use the Python API when a workflow needs to call the harness from another program, inspect returned dictionaries, or construct a config object before running.

## `simple_evaluate()`

```python
import lm_eval

results = lm_eval.simple_evaluate(
    model="hf",
    model_args={"pretrained": "gpt2", "dtype": "float32"},
    tasks=["hellaswag"],
    batch_size=1,
    device="cpu",
    limit=5,
    log_samples=False,
    random_seed=0,
    numpy_random_seed=1234,
    torch_random_seed=1234,
    fewshot_random_seed=1234,
)

if results is not None:
    print(results["results"])
```

`simple_evaluate()` may return `None` on non-primary distributed ranks. In single-process usage it returns a dictionary containing metrics, task configs, versions, sample counts, and a `config` section.

## Common Arguments

| Argument | Use |
| --- | --- |
| `model` | Backend name string or an initialized `lm_eval.api.model.LM` subclass. |
| `model_args` | String or dict; ignored for pre-initialized LM objects. |
| `tasks` | List of task names, task config dictionaries, or task objects. Required. |
| `num_fewshot` | Override few-shot count. |
| `batch_size`, `max_batch_size`, `device` | Forwarded to model construction for string model names. |
| `use_cache` | Model-response cache prefix. |
| `cache_requests`, `rewrite_requests_cache`, `delete_requests_cache` | Preprocessed request cache controls. |
| `limit` | Testing-only document limit. |
| `samples` | Exact per-task indices; mutually exclusive with `limit`. |
| `check_integrity`, `write_out` | Task validation/debug output. |
| `log_samples` | Include per-sample information in results. |
| `system_instruction`, `apply_chat_template`, `fewshot_as_multiturn` | Prompt/chat formatting. |
| `gen_kwargs` | Generation arguments for generative tasks. |
| `task_manager` | Explicit `TaskManager`, often with `include_path` for external YAML tasks. |
| `predict_only` | Generate outputs without metrics; sample logging is forced. |
| `random_seed`, `numpy_random_seed`, `torch_random_seed`, `fewshot_random_seed` | Reproducibility controls; pass `None` to skip a seed. |
| `confirm_run_unsafe_code` | Required for tasks marked as unsafe code execution. |
| `metadata` | Extra task metadata. |

## Config-Driven Python

```python
import lm_eval
from lm_eval.config.evaluate_config import EvaluatorConfig

config = EvaluatorConfig.from_config("eval.yaml")
task_manager = config.process_tasks(config.metadata)

results = lm_eval.simple_evaluate(
    model=config.model,
    model_args=config.model_args,
    tasks=config.tasks,
    num_fewshot=config.num_fewshot,
    batch_size=config.batch_size,
    max_batch_size=config.max_batch_size,
    device=config.device,
    use_cache=config.use_cache,
    cache_requests=config.cache_requests.get("cache_requests", False),
    rewrite_requests_cache=config.cache_requests.get("rewrite_requests_cache", False),
    delete_requests_cache=config.cache_requests.get("delete_requests_cache", False),
    limit=config.limit,
    samples=config.samples,
    check_integrity=config.check_integrity,
    write_out=config.write_out,
    log_samples=config.log_samples,
    system_instruction=config.system_instruction,
    apply_chat_template=config.apply_chat_template,
    fewshot_as_multiturn=config.fewshot_as_multiturn,
    gen_kwargs=config.gen_kwargs,
    task_manager=task_manager,
    predict_only=config.predict_only,
    random_seed=config.seed[0] if config.seed else None,
    numpy_random_seed=config.seed[1] if config.seed else None,
    torch_random_seed=config.seed[2] if config.seed else None,
    fewshot_random_seed=config.seed[3] if config.seed else None,
    confirm_run_unsafe_code=config.confirm_run_unsafe_code,
    metadata=config.metadata,
)
```

This mirrors the CLI run path and keeps YAML validation behavior consistent.

## External Tasks

```python
import lm_eval
from lm_eval.tasks import TaskManager

task_manager = TaskManager(include_path="task_yamls")
results = lm_eval.simple_evaluate(
    model="hf",
    model_args={"pretrained": "gpt2"},
    tasks=["my_custom_task"],
    task_manager=task_manager,
    limit=3,
)
```

If a task cannot be found, verify the task name, whether the YAML file is valid, and whether `TaskManager(include_path=...)` points at the directory containing the custom task configs.

## Low-Level `evaluate()`

Use `evaluate()` only when a caller already has an initialized `LM` object and loaded task dictionary:

```python
from lm_eval import evaluator, tasks
import lm_eval.api as api

model_args = "pretrained=gpt2,dtype=float32,device=cpu"
lm = api.registry.get_model("hf").create_from_arg_string(
    model_args,
    {"batch_size": 1, "max_batch_size": None, "device": None},
)

task_manager = tasks.TaskManager()
task_dict = task_manager.load(["hellaswag"])

results = evaluator.evaluate(
    lm=lm,
    task_dict=task_dict,
    limit=5,
    log_samples=False,
)
```

Prefer `simple_evaluate()` unless low-level control is necessary.

## Important Constraints

- Import `lm_eval.models` before relying on the full model registry in custom registry-inspection scripts.
- If both `limit` and `samples` are set, `simple_evaluate()` raises `ValueError`.
- If `tasks` is empty or resolves to no tasks, evaluation raises an error before model execution completes.
- `gen_kwargs` update generation settings only for tasks whose output type uses generation.
- `apply_chat_template` is recommended for instruct/chat models; the evaluator warns if model args look chat-like without it.
- Backend imports such as Hugging Face, vLLM, or API clients may require extras not installed in the base package.
