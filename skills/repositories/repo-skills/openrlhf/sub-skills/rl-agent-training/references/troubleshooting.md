# RL Agent Training Troubleshooting

Classify full RL runs as GPU/distributed/expensive. Prefer static command review and small template validation unless the user confirms resources and safety.

## Ray placement and resource errors

Symptoms:

- Ray actors remain pending.
- Placement groups cannot be scheduled.
- Actor, critic, reward, reference, or vLLM groups claim more GPUs than available.

Checks:

- Sum `*.num_nodes * *.num_gpus_per_node` for actor/ref/critic/reward and compare with the cluster plan.
- Account for `--vllm.num_engines * --vllm.tensor_parallel_size` unless using a validated colocated recipe.
- If using colocations, confirm `--train.colocate_actor_ref`, `--train.colocate_critic_reward`, or `--train.colocate_all` matches the desired sharing pattern.
- Use operations-and-utilities for Ray cluster startup and dashboard/job submission issues.

## vLLM engine and tensor-parallel problems

Symptoms:

- vLLM init fails.
- Weight sync hangs or crashes.
- Generation throughput is unexpectedly poor.

Checks:

- Keep `--vllm.tensor_parallel_size` compatible with GPU count per engine.
- Prefer `--vllm.sync_backend nccl` for distributed weight sync.
- Lower `--vllm.gpu_memory_utilization` if vLLM OOMs during generation.
- Use `--vllm.enforce_eager` when CUDA graph capture causes instability.
- Do not use `--vllm.enable_sleep` without `--train.colocate_all`; do not use it with async.

## NCCL and GPU visibility

Symptoms:

- DeepSpeed/vLLM sync hangs.
- Incorrect CUDA device selection inside Ray workers.
- NCCL communicator errors appear during broadcast.

Checks:

- Use operations-and-utilities for cluster-level NCCL environment setup.
- For DeepSpeed GPU index errors, consider `RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES=1` in the Ray runtime environment.
- Ensure all Ray workers see the same CUDA/NCCL stack and network interfaces.
- Be careful with vLLM versions and NCCL memory flags; avoid adding global NCCL overrides unless required by the validated environment.

## Async queue and backpressure

Symptoms:

- Sampler appears idle while trainer runs, or trainer waits on rollout.
- Memory grows with async enabled.
- Quality regresses after increasing queue size.

Checks:

- Start with `--train.async_queue_size 1`.
- Increase queue size only after convergence is validated.
- Remember that larger queues create more off-policy samples.
- If `--rollout.vllm_generate_batch_size > --rollout.batch_size`, async is required and extra generated samples are buffered.
- Pair aggressive async/partial rollout with `--algo.advantage.is_correction_enable` when appropriate.

## Partial rollout pitfalls

Symptoms:

- Training is unstable after enabling partial rollout.
- Metrics differ from synchronous/hybrid engine runs.

Checks:

- Confirm `--train.partial_rollout_enable` is only used with `--train.async_enable`.
- Treat partial rollout as the most off-policy mode because in-flight samples may span old and new weights.
- Disable partial rollout when debugging reward correctness or agent protocols.
- Compare with a synchronous or async-without-partial baseline before tuning loss hyperparameters.

## Remote reward URL shape

Symptoms:

- Rewards are missing or always zero.
- HTTP reward server logs schema errors.
- Dynamic filtering fails because scores are missing.

Checks:

- HTTP server should accept `query`, `prompts`, and `labels` arrays.
- Response should include `rewards`; include `scores` for dynamic filtering.
- Local `.py` reward functions must define `reward_func(queries, prompts, labels, **kwargs)`.
- Set `--data.label_key` when the reward needs labels.
- Keep reward endpoints reachable from Ray workers, not only from the submit shell.

## Reward function import path

Symptoms:

- `reward_func` import fails.
- A local path works outside Ray but fails inside training.

Checks:

- The reward file path passed to `--reward.remote_url` must exist in the Ray runtime working directory or be an absolute path valid on every worker.
- The function name must be exactly `reward_func`.
- Install any reward dependencies in the Ray runtime environment.
- Avoid relying on notebook globals or source-relative imports that are not shipped to workers.

## Agent reset/step protocol errors

Symptoms:

- Multi-turn rollout crashes with missing dict keys.
- Rollout completes but no action tokens are trained.
- Rewards are not scalar/tensor-like.

Checks:

- The agent file must export class `AgentExecutor`.
- For `MultiTurnAgentExecutor`, `AgentInstance.reset()` should return `{"observation": text}`.
- `AgentInstance.step()` must return `rewards`, `environment_feedback`, and `done`; include `scores` for dynamic filtering.
- Keep `environment_feedback` formatted as the next user/environment turn plus assistant prefix when the model expects chat formatting.
- Final reward should usually be assigned when `done=True`; intermediate rewards are often zero unless dense rewards are intended.

## OpenAI-compatible executor issues

Symptoms:

- Token traces are empty.
- Prefix consistency assertions fail.
- Custom agent calls local server but rollouts cannot be stitched.

Checks:

- Every chat-completions call in one episode must pass the same `session_id` in the request body extras.
- Avoid rewriting earlier messages in a way that changes tokenized prefixes; the executor assumes prefix stability.
- Request logprobs when the training path needs rollout log probabilities.
- Confirm FastAPI/uvicorn/openai dependencies are installed on Ray workers.

## VLM image/media mismatch

Symptoms:

- VLM prompt truncation errors mention image token alignment.
- vLLM complains about multimodal placeholders.
- Training crashes when packing is enabled.

Checks:

- Use `--data.max_images_per_prompt > 0` and set the correct `--data.image_key`.
- Use a non-`gae` estimator; VLM training does not support critic training.
- Do not enable `--ds.packing_samples` for VLM runs.
- Ensure each returned `environment_images` item has a matching model-specific image placeholder in `environment_feedback`.
- Increase `--data.max_len` or reduce `--rollout.max_new_tokens` instead of truncating VLM prompts.

## KL and advantage misuse

Symptoms:

- Training silently makes no progress.
- Advantages are always zero.
- KL behavior looks inconsistent with the selected algorithm.

Checks:

- `rloo`, `reinforce_baseline`, `group_norm`, and `dr_grpo` require `--rollout.n_samples_per_prompt > 1`; with one sample per prompt, group baselines collapse.
- PPO with `gae` needs a critic; non-`gae` estimators disable critic model usage.
- Use `--algo.kl.use_loss` only intentionally, and prefer `k2`/`k3` with it.
- Use `k1` when KL is not used as a loss.
- Do not set `--algo.kl.init_coef 0` unless reference-free training is intended.

## OOM and batch sizing

Symptoms:

- CUDA OOM during generation, reward, critic, or actor update.
- OOM occurs only after enabling multi-sample rollout or VLM.

Checks:

- Reduce `--rollout.micro_batch_size` or `--train.micro_batch_size` first.
- Reduce `--rollout.batch_size`, `--train.batch_size`, or `--rollout.n_samples_per_prompt` if memory pressure remains.
- Lower `--data.max_len` or `--rollout.max_new_tokens` for long rollouts.
- Lower `--vllm.gpu_memory_utilization` for vLLM memory conflicts.
- Use gradient checkpointing for actor memory pressure.
- For text-only dynamic batching, use `--train.dynamic_batch_enable` and token budgets; for VLM, do not use packing.
