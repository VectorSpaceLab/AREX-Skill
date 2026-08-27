# Extension troubleshooting

Use this table when an RLinf extension fails during config validation, worker startup, rollout, training, install, or CI.

## Registration and distributed worker failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Model Type: ... not supported` during validation | `SupportedModel` did not see the new model type. | For external models, call `register_model(...)` before validation and from `RLINF_EXT_MODULE.register()`. For core models, add registry wiring and ensure the string matches YAML exactly. |
| `get_model(cfg)` returns `None` | `SupportedModel` may be registered but no builder exists in the model registry. | Use `register_model(...)` rather than only `SupportedModel.register(...)`, or add the builder to core model registry wiring. |
| Driver can build model but Ray worker cannot | Registration only ran in the driver process. | Put registrations in an importable extension module with `register()` and set `RLINF_EXT_MODULE` anywhere workers or conversion tools run. |
| `Extension module ... has no register()` warning | `RLINF_EXT_MODULE` points to a module without a callable `register`. | Add `def register(): ...` and keep it idempotent. |
| Reward/parser/tool lookup says not registered | The module containing decorator registration was never imported in that process. | Import it in core init code or from `RLINF_EXT_MODULE.register()` before the worker lookup. |
| Custom env string fails before factory branch | `SupportedEnvType` enum does not include it. | Add a core enum value and a lazy `get_env_cls(...)` branch; external env registration is not enough for the current enum validator. |

## Config validation failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Actor-critic loss rejects config | PPO actor-critic paths require a value head or critic support. | Set the required value-head config, add a critic, or choose a loss compatible with the model. Add validation for custom losses. |
| Training pipeline rejects advantage type | Some pipeline modes only support `gae`. | Use a supported advantage or implement/validate the new pipeline behavior explicitly. |
| Env total number not divisible | `total_num_envs`, env world size, pipeline stages, or `group_size` mismatch. | Choose values divisible by all relevant dimensions and test both train/eval configs. |
| Megatron checkpoint validation fails | Config provides neither a converted Megatron checkpoint nor a valid HF conversion path, or parallel sizes are incompatible. | Set `use_hf_ckpt` with conversion config for first run, or provide `megatron_checkpoint`; verify tensor/pipeline parallel divisibility. |
| API reward worker rejects model type | `reward.worker_type: api` is used with a non-buffered VLM reward model. | Use `reward.model.model_type: buffered_vlm` for API reward paths or implement a new validated worker path. |
| Ray-managed reward API lacks placement | Empty external API base means RLinf must launch a reward server, but placement is absent. | Add reward-server placement or provide an external API base. |

## Model and FSDP failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| FSDP wraps too little or OOMs | Custom blocks, vision tower, projector, or value head are not in wrap policy. | Add explicit `fsdp_config.wrap_policy` with transformer layer class names, extra module classes, and `no_split_names` for named modules. |
| Value head not trained | LoRA/FSDP wrapping or model construction leaves value head frozen or outside training path. | Verify `requires_grad`, model output includes `values`, loss expects value, and wrap policy includes the head where needed. |
| Training recompute lacks fields | `predict_action_batch(...)` did not preserve enough `forward_inputs` for `default_forward(...)`. | Cache all observation/action/sampling fields needed to recompute logprobs, values, and entropy. |
| Rollout actions have wrong sign or shape | Model/env action semantics mismatch. | Decide whether the model should output final executable actions or add a precise `prepare_actions(...)` branch. Test gripper sign, slicing, chunking, and dtype. |
| SFT worker crashes on batch | Collate output does not match `get_train_model_output(...)` or eval fields. | Make train/eval dataloaders produce consistent dict keys and test one batch through train and eval methods. |

## Environment failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Heavy simulator imports break normal package import | Env module imports simulator dependencies at top level. | Keep imports lazy inside `get_env_cls(...)` or env initialization paths. |
| Offload restore changes rollout behavior | Serialized state misses RNG, task state, wrapper state, or simulator internal state. | Include env state, RNG state, episode counters, and wrapper state in `get_state`/`load_state` tests. |
| Evaluation works but training hangs | Train env vectorization/grouping differs from eval; action chunks or pipeline stages mismatch. | Validate train/eval env counts, rollout epochs, `max_steps_per_rollout_epoch`, and chunk divisibility. |
| New env works locally but not in CI | Install script omitted env dependencies/assets or CI runner lacks hardware. | Add install target coverage and skip/mark hardware-specific e2e with clear prerequisites. |

## Worker and runner failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Worker constructed in driver raises or lacks rank fields | Worker subclass was instantiated directly. | Always launch through `create_group(...).launch(...)`. Put remote setup in `init_worker(...)`. |
| NCCL/GLOO communication hangs | Mismatched send/recv order, tensor device mix, or async operation pairing. | Pair sends/receives exactly, avoid mixed CPU/GPU tensor containers, and keep collective options consistent. |
| Metrics missing or duplicated | Runner or worker returns inconsistent metric dicts by rank. | Decide rank aggregation strategy, prefix metrics consistently, and detach tensors before logging. |
| Resume fails from checkpoint path | Runner checkpoint layout or global-step parsing differs from existing convention. | Preserve `global_step_<N>/actor` style where compatible and test save/resume paths. |

## Install, Docker, and CI failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `install.sh --model` rejects new model | Supported model selector was not added or name differs from docs. | Add the selector and document mapping to runtime `model_type`. |
| `install.sh --env` rejects new env | Supported env selector or env-only branch missing. | Add the env selector and an `install_env_only` branch when env-only installs are supported. |
| Docker build cannot resolve target | Dockerfile stage name does not match `BUILD_TARGET` or CI job argument. | Align `base-image-*`, `*-image`, CI job id, tag, and docs target names. |
| Docker uv cache/hardlink failure after multi-venv install | Installs split across layers while expecting hardlinked cache. | Chain related install commands in one `RUN` where the Docker pattern requires it. |
| CI does not run for new files | Central path filters do not include the new source/test/doc locations. | Update the relevant change filters and reusable workflow jobs. |
| E2E is too expensive or flaky | Config uses full dataset/model/env settings instead of a smoke-size test. | Reduce steps/envs/batch sizes, use tiny assets where possible, and document any required hardware/dataset skip. |

## Documentation and contribution failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Docs mention commands that do not install dependencies | Install/Docker support was not updated with the example. | Add matching install selectors, Docker target, and prerequisites before publishing quick start docs. |
| English and Chinese docs diverge | Only one language was updated. | Update both or record why a page is intentionally unavailable. |
| Commit check fails | Missing Signed-off-by or invalid Conventional Commit format. | Amend with `git commit --amend -s` and use `<type>(<scope>): <description>`. |
| PR title check fails | Title description too long, not lowercase imperative, non-ASCII, or invalid scope chars. | Shorten and normalize the PR title before requesting review. |
