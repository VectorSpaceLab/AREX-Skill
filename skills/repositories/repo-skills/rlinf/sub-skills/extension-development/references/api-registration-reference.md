# API and registration reference

Use this as a compact map of RLinf extension touchpoints. It is intentionally self-contained; treat paths as implementation touchpoints, not as runtime links.

## Core validation constants and config selectors

| Surface | Selector/config field | Validation / dispatch touchpoint | Notes |
| --- | --- | --- | --- |
| Task type | `runner.task_type` | `SUPPORTED_TASK_TYPE`; `validate_cfg(...)` branch | Values include embodied, embodied_eval, reasoning, reasoning_eval, coding_online_rl, sft, and offline. New task types require core validation and entrypoint wiring. |
| Training backend | `actor.training_backend`, optional `critic.training_backend` | `SUPPORTED_TRAINING_BACKENDS`; FSDP/Megatron validation | Values are `fsdp` and `megatron`. Backend-specific model and checkpoint requirements are validated later. |
| Rollout backend | `rollout.rollout_backend` | rollout validation | Values are `sglang` and `vllm`. Agentic install environments may need separate venvs because engines pin incompatible kernel stacks. |
| Embodied model | `actor.model.model_type`, `rollout.model.model_type` | `SupportedModel`, `EMBODIED_MODEL`, model registry | Use `register_model(...)` for external or core registration. |
| Environment | `env.train.env_type`, `env.eval.env_type` | `SupportedEnvType`; `get_env_cls(...)` | New env types normally need a core enum/factory edit. |
| Advantage | `algorithm.adv_type` | `register_advantage`, `calculate_adv_and_returns(...)` | Registered lowercase. Some validation requires group size or disallows non-GAE modes in training pipeline. |
| Policy loss | `algorithm.loss_type` | `register_policy_loss`, `policy_loss(...)` | Registered lowercase; YAML should be lowercase because lookup is exact. PPO actor-critic losses require value head validation. |
| Rule-based text reward | `reward.reward_type` when `reward.use_reward_model` is false | `register_reward`, `get_rule_based_reward_class(...)` | Reward workers instantiate by name during `init_worker()`. |
| Embodied reward model | `reward.model.model_type` | reward model registry | Built-ins include `resnet`, `vlm`, and `buffered_vlm`. |
| VLM reward input/parser | `reward.model.input_builder_name`, `reward.model.reward_parser_name` | input-builder and reward-parser registries | External decorators must be imported before worker lookup. |
| Tool-call parser | parser config used by agent/tool stack | `register_toolcall_parser`, `get_toolcall_parser(...)` | Lookup imports built-in parser modules lazily if registry is empty. |

## Model registration

`register_model(model_type, model_builder, category="embodied", force=False)` is the preferred extension API for new models. It performs three important actions:

1. Stores the builder in the model registry used by `get_model(cfg)`.
2. Registers the string with `SupportedModel` so config validation can resolve it.
3. Adds the model to the embodied-model set when `category="embodied"`.

Builder contract:

```python
def build_model(cfg, torch_dtype):
    # construct and return a model instance
    return model
```

`get_model(cfg)` reads `cfg.model_type`, derives `torch_dtype` from `cfg.precision`, calls the registered builder, moves the model to the worker device when appropriate, and applies LoRA handling when `cfg.is_lora` is true.

### External distributed registration with `RLINF_EXT_MODULE`

Ray workers do not inherit driver-local Python registrations. Put all external registrations in an importable module:

```python
from rlinf.models import register_model


def register():
    register_model("my_model", build_model, category="embodied")
    # Import or call any extra algorithm/reward/parser registration here too.
```

Then set `RLINF_EXT_MODULE` to that module path anywhere RLinf worker or checkpoint-conversion processes run. RLinf imports the module and calls `register()` during worker initialization. Missing, misspelled, or non-importable extension modules are a common source of `model_type not supported`, `get_model(...) is None`, or registry lookup failures.

### Built-in model touchpoints

Core model additions typically touch these concepts:

- A model package with a `get_model(cfg, torch_dtype)` builder.
- Model registry wiring so `get_model(cfg)` can resolve the new string.
- `BasePolicy` compatibility for embodied RL models.
- FSDP wrap-policy config for transformer blocks, vision towers, projectors, value heads, or custom `_fsdp_wrap_name` modules.
- Action conversion expectations between `predict_action_batch(...)`, `forward_inputs`, and `prepare_actions(...)`.
- SFT or Megatron-specific workers/managers when those backends are in scope.

## `BasePolicy` contract

`BasePolicy` defines a dispatch surface with `ForwardType` values such as default, SFT, SAC, SAC_Q, CROSSQ, IQL, and NFT. A direct subclass must implement:

- `default_forward(**kwargs)`: recomputes logprobs/values/entropy or other training outputs from cached rollout inputs.
- `predict_action_batch(**kwargs)`: turns environment observations into action chunks plus metadata needed for later training.

Optional branches (`sac_forward`, `crossq_forward`, `iql_forward`, `prepare_dagger_sft_batch`, etc.) should be implemented only when the selected algorithms call them. If a model advertises a config/algorithm combination but leaves the needed branch unimplemented, the failure will happen inside remote actor/rollout workers.

## Algorithm registries

### Advantage registry

- Register with `@register_advantage("name")`.
- Dispatch with `calculate_adv_and_returns(adv_type="name", task_type=..., ...)`.
- Return a tuple `(advantages, returns)`.
- Embodied paths pre-process tensors and post-process outputs; some non-GAE modes first compute scores.
- Reasoning paths have a separate pre/post-processing path.

### Policy loss registry

- Register with `@register_policy_loss("name")`.
- Dispatch with `policy_loss(loss_type="name", task_type=..., ...)`.
- Return `(loss_tensor, metrics_dict)`.
- Existing actor workers pass different kwargs depending on backend/task; keep the function tolerant only where the algorithm contract says so, not by swallowing errors silently.

### Loss-scale registry

- Register custom loss-scale processors with `register_loss_scale("name")` when the task explicitly uses loss scale processing.
- Lookup requires every configured name to be registered.

## Reward and parser registries

### Rule-based rewards

Register classes with `register_reward(name, reward_class)`. The class is instantiated with the reward config and should expose `get_reward(...)`. Keep return order exactly aligned to input batch order.

### Embodied reward models

The embodied reward worker obtains reward classes from the reward-model registry. Built-in classes include ResNet, VLM, and buffered VLM reward models. New core reward models should implement the base reward model interface and return tensors with per-env rewards.

### VLM input builders and reward parsers

Input builders and parsers are decorator-registered by lowercase names:

- `register_input_builder("name")` for classes that prepare images/videos/text prompts from observations.
- `register_reward_parser("name")` for classes that parse model/API outputs into reward tensors.

When used by API reward workers, `reward.worker_type: api` currently expects `reward.model.model_type: buffered_vlm`. If the API base is not provided, the config must include a Ray-managed reward-server placement.

### Tool-call parsers

`register_toolcall_parser("name")` stores parser classes for agent/tool workflows. `get_toolcall_parser(name)` returns an instance. External parsers need module import before lookup, normally through `RLINF_EXT_MODULE.register()` for distributed use.

## Environment factory and action conversion

### Environment factory

`SupportedEnvType` enumerates valid environment strings. `get_env_cls(env_type, env_cfg=None)` converts the string into that enum and returns an environment class by lazy import. Heavy simulator imports should remain inside branches.

Special patterns to preserve:

- Env-specific task validation can happen inside `get_env_cls(...)` when a task id maps to registered env classes.
- Offload variants should be selected by config flags such as `enable_offload` without importing both heavy implementations prematurely.
- The fallback error should make the unsupported env type explicit.

### Action conversion

`prepare_actions(...)` normalizes torch tensors to CPU numpy arrays before dispatching by `SupportedEnvType`. Branch helpers may return numpy arrays or torch tensors depending on env requirements. When adding a new env/model combination, verify:

- Last-dimension action semantics (gripper sign, binary open/close, action slices, padding).
- Action chunk shape: `[batch, num_action_chunks, action_dim]` or env-specific equivalent.
- `action_dim`, `action_scale`, `policy`, `wm_env_type`, and `env_cfg` usage.
- Whether a new model should emit final actions directly rather than adding env-side branches.

## Worker and runner APIs

### Worker launch

`Worker.create_group(*args, **kwargs)` returns a `WorkerGroup`. Launch it with cluster, placement strategy, and a unique name. Do not instantiate a worker directly in driver code. Worker launch sets rank, world size, local rank, node group, hardware ranks, device context, logging, timers, and communication metadata.

### Worker communication

- Use `Channel.create(...)` for runner-mediated producer/consumer flow.
- Use `send`/`recv` or tensor-specific variants for direct worker-to-worker transfers.
- Match NCCL/GLOO expectations: avoid mixing CPU and GPU tensors in optimized tensor containers and pair async sends/receives carefully.

### Logging

Inside workers, use `self.log_info(...)`, `self.log_warning(...)`, and `self.log_error(...)`. Outside workers, use RLinf's logger helper or Python logging. Avoid adding production `print(...)` calls.

### Runner ownership

Runners own global step, worker initialization order, channels, rollout/reward/advantage/update loop, metric logging, eval cadence, save/resume, and shutdown. A new runner should not hide config mutation in worker code; validation and defaults belong in config validation.

## Config validation touchpoints

Add validation whenever an extension introduces a new user-facing config field or incompatible combination. Typical checks:

- Model type must be supported and in the correct category.
- Env type must resolve and train/eval env counts must divide by world size, pipeline stage count, and group size.
- Actor global batch size must divide by micro batch size times actor world size.
- Actor-critic losses need value-head or critic support.
- Pipeline modes and reward model modes can be mutually incompatible.
- Megatron requires checkpoint conversion or an explicit converted checkpoint, tensor/pipeline parallel divisibility, and HF config compatibility.
- Hardware-only envs should fail early with clear requirements or documented skips.
