# API reference

This reference captures the public Python entry points that future agents are most likely to use when they work programmatically with lmms-eval instead of through the CLI.

## Programmatic evaluation

### `simple_evaluate`

```python
simple_evaluate(
    model,
    model_args=None,
    launcher_args=None,
    tasks=None,
    num_fewshot=None,
    batch_size=None,
    max_batch_size=None,
    device=None,
    use_cache=None,
    cache_requests=False,
    rewrite_requests_cache=False,
    delete_requests_cache=False,
    limit=None,
    offset=0,
    bootstrap_iters=100000,
    check_integrity=False,
    write_out=False,
    log_samples=True,
    evaluation_tracker=None,
    system_instruction=None,
    apply_chat_template=False,
    fewshot_as_multiturn=False,
    gen_kwargs=None,
    task_manager=None,
    verbosity="INFO",
    predict_only=False,
    random_seed=0,
    numpy_random_seed=1234,
    torch_random_seed=1234,
    fewshot_random_seed=1234,
    datetime_str="...",
    distributed_executor_backend="accelerate",
    cli_args=None,
    force_simple=False,
    repeats=1,
    baseline=None,
    max_tokens=None,
)
```

Use this when you want the package to handle model loading, task lookup, cache control, and result aggregation for you.

### `evaluate`

```python
evaluate(
    lm,
    task_dict,
    limit=None,
    offset=0,
    cache_requests=False,
    rewrite_requests_cache=False,
    bootstrap_iters=100000,
    write_out=False,
    log_samples=True,
    system_instruction=None,
    apply_chat_template=False,
    fewshot_as_multiturn=False,
    verbosity="INFO",
    distributed_executor_backend="accelerate",
    eval_server_launcher=None,
    cli_args=None,
    response_cache=None,
)
```

Use this when you already have a loaded model object and a task dictionary.

## Task loading and registry

### `TaskManager`

```python
TaskManager(
    verbosity="INFO",
    include_path=None,
    include_defaults=True,
    model_name=None,
)
```

Important runtime attributes include:

- `all_subtasks`
- `all_groups`
- `all_tags`
- `task_index`

### `get_task_dict`

```python
get_task_dict(task_name_list, task_manager=None, task_type="simple")
```

Use `task_type="chat"` when the task uses `doc_to_messages`. Use `task_type="simple"` when the task still relies on simple text/visual request shapes.

## Message and media protocol

### `ChatMessages`

```python
ChatMessages(messages=raw_messages)
```

Common methods:

- `extract_media()`
- `to_hf_messages(video_kwargs=None, image_kwargs=None)`
- `to_openai_messages(video_kwargs=None, pass_video_url=False)`
- `to_qwen3_vl_openai_messages(video_kwargs=None)`

The class is the canonical multimodal message container for chat-style model backends.

## Request shapes

The current runtime expects model methods to unpack `Instance.args` in these shapes:

| Output type | Simple model shape | Chat model shape |
| --- | --- | --- |
| `generate_until` | `(ctx, gen_kwargs, doc_to_visual, doc_id, task, split)` | `(ctx, doc_to_messages, gen_kwargs, doc_id, task, split)` |
| `loglikelihood` | `(ctx, doc_to_target, doc_to_visual, doc_id, task, split)` | same shape |
| `generate_until_multi_round` | `(ctx, gen_kwargs, doc_to_visual, doc_to_text, doc_id, task, split)` | same shape |
| `generate_until_agentic` | `(ctx, gen_kwargs, doc_to_visual, doc_to_text, doc_id, task, split)` | same shape |

## Service layer APIs

### `ServerArgs`

The server configuration object currently round-trips with fields like:

- `host`
- `port`
- `max_completed_jobs`
- `temp_dir_prefix`

### `EvalClient` and `AsyncEvalClient`

Common evaluation entry point:

```python
EvalClient.evaluate(
    self,
    model,
    tasks,
    model_args=None,
    num_fewshot=None,
    batch_size=None,
    device=None,
    limit=None,
    gen_kwargs=None,
    log_samples=True,
    predict_only=False,
    num_gpus=1,
    output_dir=None,
)
```

The async client mirrors the same intent with `await client.evaluate(...)`.

### `JobScheduler`

The scheduler owns the queued evaluation lifecycle. Common methods include:

- `start()`
- `stop()`
- `add_job(request)`
- `get_job(job_id)`
- `get_job_with_position(job_id)`
- `cancel_job(job_id)`
- `get_queue_stats()`
- `cleanup_old_jobs()`

## Reasoning and cache helpers

- `strip_reasoning_tags(text, tag_pairs)` removes reasoning blocks before scoring.
- `parse_reasoning_tags_config(cli_value=None, task_value=None)` resolves CLI and task overrides.
- `canonicalize_gen_kwargs(gen_kwargs)` normalizes generation kwargs for caching.
- `is_deterministic(request_type, gen_kwargs)` decides whether a request is safe to cache.

## Practical selection guidance

- Use `simple_evaluate` for the common end-to-end path.
- Use `evaluate` only when your code already built the lower-level model and task structures.
- Use `TaskManager` and `get_task_dict` when you need to inspect or assemble task objects without launching a full CLI run.
- Use the service-layer objects when you need asynchronous evaluation or long-running jobs.
