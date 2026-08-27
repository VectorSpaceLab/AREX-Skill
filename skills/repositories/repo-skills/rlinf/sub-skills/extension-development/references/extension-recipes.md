# RLinf extension recipes

This reference turns RLinf extension evidence into operating recipes. Use it with [api-registration-reference.md](api-registration-reference.md), [install-docker-ci-docs.md](install-docker-ci-docs.md), [contributor-guidance.md](contributor-guidance.md), and [troubleshooting.md](troubleshooting.md).

## Choose the extension mode first

| Mode | Use when | Key consequence |
| --- | --- | --- |
| External package / experiment | The change should live outside RLinf core but still run inside RLinf workers. | Prefer registry APIs and an importable `RLINF_EXT_MODULE` with a `register()` function. Worker processes must be able to import the module. |
| RLinf core contribution | The capability is intended to ship with RLinf or requires enums/factories/CI/docs in core. | Edit the relevant core touchpoints, add validation, tests, install/Docker/CI/docs coverage, and follow contributor rules. |
| Prototype-only patch | The user explicitly asks for a local experiment without public support. | Keep the patch narrow, still avoid distributed registration traps, and mark missing install/docs/CI as intentional gaps. |

Model, algorithm, rule-based reward, reward-parser, and input-builder extensions can often be external. Environments and new task types usually require core edits because RLinf validates environment type and task type through core registries/enums and entrypoint wiring.

## Algorithm, advantage, loss, reward, and tool-parser recipe

### Advantage functions

1. Implement a pure tensor function that accepts the keyword arguments supplied by `calculate_adv_and_returns(...)` for the selected task family.
2. Register it with `register_advantage("your_adv")`. Names are stored lowercase; use lowercase config values.
3. Return `(advantages, returns)`. Shape and mask handling must match existing algorithms: embodied inputs are pre/post-processed and non-GAE advantages may receive score fields first; reasoning inputs are preprocessed separately.
4. Wire the config with `algorithm.adv_type: your_adv` and add validation if the algorithm needs a group size, bootstrap value, rollout field, or incompatible runner mode.
5. Test both the raw function and the registry dispatch path. Include shape/mask tests and a config validation failure test for bad combinations.

### Policy losses

1. Implement a function that accepts the kwargs passed to `policy_loss(...)` for the relevant actor worker and returns `(loss_tensor, metrics_dict)`.
2. Register it with `register_policy_loss("your_loss")`; use a lowercase YAML value because lookup is exact after registration stores lowercase names.
3. Preserve metric naming conventions such as `actor/...` and detach metric tensors before returning them.
4. Set `algorithm.loss_type: your_loss`. Add validation for required model heads, critic availability, clipping parameters, masks, or runner restrictions.
5. Test the function, registry dispatch, and actor-worker call path. For embodied losses, verify preprocessing/postprocessing expectations; for reasoning losses, verify token masks and batch dimensions.

### Rule-based rewards for reasoning/agentic tasks

1. Implement a reward class with `__init__(config)` and `get_reward(...)` matching the data path you will use. Existing rewards accept response/completion text plus references/answers and sometimes prompts.
2. Register it with `register_reward("your_reward", YourRewardClass)` before `RewardWorker.init_worker()` runs.
3. Set the config reward selector used by the runner, commonly `reward.reward_type: your_reward` when `reward.use_reward_model` is false.
4. If the reward is external, import its registration in `RLINF_EXT_MODULE.register()` so Ray reward workers see it.
5. Include timeout/error behavior for expensive or sandboxed reward checks and unit tests for malformed answers, empty outputs, and batch order preservation.

### Tool-call parsers

1. Implement a parser class with the same public contract as the existing tool-call parser family.
2. Decorate it with `register_toolcall_parser("your_parser")` or import a module that performs that decoration.
3. Ensure the parser module is imported before lookup. For external distributed use, load it from `RLINF_EXT_MODULE.register()`.
4. Test malformed tool calls, multiple calls, and the exact config field that selects the parser.

## Embodied model recipe

### External registration path

Use this when another package depends on RLinf and should not patch RLinf core.

1. Write a builder `build_model(cfg, torch_dtype)` that returns the model instance.
2. Call `register_model("your_model_type", build_model, category="embodied")`. This registers `SupportedModel`, adds the value to the embodied-model set, and routes `get_model(cfg)`.
3. Put that call inside a module-level `register()` function in an importable extension module.
4. Export `RLINF_EXT_MODULE=<module.path>` in the driver environment and in any execution environment used by checkpoint conversion or Ray workers.
5. Use `actor.model.model_type` / `rollout.model.model_type` in YAML exactly as registered.

This path is the safest way to avoid editing `SupportedModel` directly. It still requires the extension package to be importable on every Ray worker and any standalone utility process that calls `get_model(...)`.

### Core built-in model path

Use this when the model should ship inside RLinf.

1. Add or reuse a package under the embodied model namespace with a `get_model(cfg, torch_dtype)`-style builder.
2. Register the builder in the model registry and ensure the model type is included in the embodied model set. Existing built-ins also expose `SupportedModel.<NAME>` constants for readability.
3. Implement the policy contract. For `BasePolicy`, implement `default_forward(...)` and `predict_action_batch(...)`; keep `forward(...)` dispatch compatible with PPO/SFT/SAC/IQL/NFT paths when those algorithms are in scope.
4. `predict_action_batch(...)` must return executable actions plus a result dict with all fields needed to recompute training logprobs/values/entropy in `default_forward(...)`.
5. If the model returns final environment actions, prefer doing post-processing inside the model instead of adding a new branch for every model in environment action conversion.
6. Add FSDP wrap-policy config when class names or named submodules must be sharded separately. Use explicit transformer layer names, extra module class names, and `_fsdp_wrap_name`/`no_split_names` for value heads or projectors.
7. For Megatron training, confirm Megatron-LM supports the architecture, then cover model provider, checkpoint conversion from HuggingFace to Megatron, rollout-engine compatibility, and weight sync from actor to SGLang/vLLM.
8. Add unit tests for model registration/building and FSDP wrap policy. Add e2e only for the smallest feasible model/env/algorithm combination or document hardware/dataset constraints.

### SFT-specific model path

1. Ensure `get_model(actor.model)` returns a model whose training forward returns a scalar loss or stackable losses.
2. If a custom SFT worker is needed, subclass the FSDP SFT worker family and implement dataloader construction, train output, and eval output.
3. Keep batch keys produced by collate functions aligned with `get_train_model_output(...)` and `get_eval_model_output(...)`.
4. Add SFT config and e2e coverage when the change is user-facing.

## Environment recipe

1. Add a core environment type value. RLinf validates env strings through `SupportedEnvType`, so a new env normally needs a core enum entry rather than only external registration.
2. Add a `get_env_cls(env_type, env_cfg=None)` branch with a lazy import. Do not import heavyweight simulator packages at module import time.
3. Implement a gym-style env class with constructor fields compatible with RLinf workers: config, rank, vectorized `num_envs`, `group_size`, seed, and return device. Provide `reset(...)`, `step(...)`, observation/action spaces, reward/success/termination/truncation info, and deterministic reset handling where possible.
4. If environment state save/restore or simulator offload is required, implement state serialization and loading in a separate wrapper or offload variant and gate it with config such as `enable_offload`.
5. Add an action conversion helper only when the environment cannot consume the model's returned actions directly. The central `prepare_actions(...)` path converts torch tensors to CPU numpy first, then dispatches by env type; return numpy or torch according to the existing environment's expectations.
6. Add train/eval config presets with static YAML values. Include `env.train.env_type`, `env.eval.env_type`, `total_num_envs`, `group_size`, `max_steps_per_rollout_epoch`, `rollout_epoch`, and env-specific `init_params`.
7. Add validation for env-specific invariants: task id registration, group divisibility, required paths, supported robots, incompatible offload/pipeline settings, or hardware-only modes.
8. Add install support, Docker/CI/e2e coverage, docs, and asset/environment variable notes for user-facing envs.

## Embodied reward model and reward parser recipe

RLinf has two reward surfaces:

- Rule-based text rewards for reasoning/agentic rollouts, registered through the algorithm reward registry.
- Embodied reward models, input builders, and parsers used by embodied reward workers.

For embodied reward models:

1. Decide whether the model is a core reward model class or a configurable input-builder/parser on top of an existing VLM/buffered VLM path.
2. For a new reward model class, update the reward-model registry and implement `compute_reward(observations)` returning a tensor shaped for the env batch.
3. For VLM/buffered VLM customization, register input builders and reward parsers, then select them in `reward.model.input_builder_name` and `reward.model.reward_parser_name`.
4. Respect validation gates: API reward workers currently require `reward.worker_type: api` with `reward.model.model_type: buffered_vlm`; Ray-managed SGLang reward APIs require a reward server placement when no external API base is provided.
5. Verify history-buffer modes, interval rewards before enough history exists, invalid parser outputs, and local/API parity if both modes are supported.

## Worker, runner, and task-type recipe

### Workers

1. Subclass `Worker` or an existing worker manager class. Put heavyweight initialization in an `init_worker(...)`/initialization method invoked remotely, not in driver-only code.
2. Launch with `YourWorker.create_group(...).launch(cluster=cluster, placement_strategy=..., name="...")`.
3. Use worker rank/world-size/device fields set by RLinf. Do not assume driver-local CUDA state.
4. Use `Channel` for runner-mediated flows and `send`/`recv` for direct worker-to-worker communication. Match send/recv shapes, devices, async behavior, and collective options on both sides.
5. Use `self.log_info`, `self.log_warning`, and `self.log_error` inside workers.

### Runners

1. Let the runner own the training/evaluation loop, global step, worker coordination, channels, timers, metric logging, checkpoint save/resume, and validation cadence.
2. New task types need an entry script that validates config, builds `Cluster`, builds the correct placement object, launches worker groups, constructs the runner, and calls `runner.run()` or `runner.run_eval()`.
3. Add the task type to config validation and define backend compatibility. Do not bypass `validate_cfg(...)` to make an example work.
4. Reuse existing placement patterns where possible: model-parallel placement for reasoning/agentic tasks and hybrid placement for embodied tasks.
5. Include a fast unit-level test for config/runner wiring and an e2e config if the task is public.

## Completion gate for any extension

Before handing off an extension, answer all of these:

- What registry or factory selects the new capability?
- Does the selection happen in the driver only, workers only, or both?
- If external, how do Ray workers import the registration?
- Which config fields select the extension, and what validation catches bad combinations?
- Which action/reward/model batch shapes are expected and tested?
- Which install target, Docker target, CI filter/job, docs page, and e2e config cover it?
- Which hardware or dataset assumptions remain unresolved?
