# Training and Config Troubleshooting

## Hydra Override Problems

- **Symptom**: `Key '...' is not in struct` or Hydra rejects an override.
  **Fix**: Use existing keys as `key=value`; use `+key=value` only for truly new fields. Quote list values such as `trainer.logger='["console","wandb"]'` and `data.train_files='["/a.parquet","/b.parquet"]'`.

- **Symptom**: Shell splits list values or strips quotes.
  **Fix**: Wrap JSON-like lists in single quotes, or construct bash arrays with each Hydra override as one array element.

- **Symptom**: Config field names differ between examples.
  **Fix**: Check which backend owns the field. FSDP examples use `fsdp_config`/`fsdp`; Megatron uses `.megatron.*`; TorchTitan and VeOmni have their own nested engine configs.

## Overlong Prompts and Truncation

- **Symptom**: Training fails when a prompt exceeds `data.max_prompt_length`.
  **Cause**: `data.truncation=error` intentionally fails rather than silently shortening input.
  **Fix**: Increase `data.max_prompt_length`, enable `data.filter_overlong_prompts=True`, or deliberately choose `data.truncation=left`, `right`, or `middle` after confirming that truncation is acceptable for the task.

- **Difficult case to test**: Keep `data.truncation=error`, set a small `data.max_prompt_length`, and verify the agent explains why long prompts should fail rather than recommending blind truncation.

## GPU and Memory Failures

- **Symptom**: CUDA/NPU OOM during actor update, critic update, reference log-prob, or rollout.
  **Fixes**: Lower `ppo_micro_batch_size_per_gpu`, enable `use_dynamic_bsz`, reduce `ppo_max_token_len_per_gpu`, lower `actor_rollout_ref.rollout.gpu_memory_utilization`, enable gradient checkpointing, enable parameter/optimizer offload, reduce `rollout.n`, or use a smaller model/debug dataset.

- **Symptom**: Rollout backend allocates too much memory before training starts.
  **Fixes**: Reduce `actor_rollout_ref.rollout.tensor_model_parallel_size` only if still compatible with model size, lower `gpu_memory_utilization`, reduce `max_num_batched_tokens`/`max_num_seqs` when configured, or choose a lighter backend for debugging.

- **Symptom**: A multi-node or 8-GPU example must be debugged on one GPU.
  **Fix**: Reduce `trainer.n_gpus_per_node=1`, `trainer.nnodes=1`, rollout TP to 1, batch sizes to tiny values, micro-batch size to 1, save frequency to `-1`, and use `trainer.logger=console`. Do not preserve production batch sizes.

## PPO vs GRPO Misconfiguration

- **Symptom**: PPO command has no critic settings.
  **Fix**: Add `critic.model.path`, `critic.optim.lr`, and critic batch/offload settings, or intentionally convert to GRPO and remove critic assumptions.

- **Symptom**: GRPO behaves like single-sample PPO.
  **Fix**: Set `algorithm.adv_estimator=grpo`, use `actor_rollout_ref.rollout.n>1`, enable actor KL loss if desired, and ensure grouped rewards are meaningful.

- **Symptom**: KL is applied twice or in the wrong place.
  **Fix**: Choose either in-reward KL (`algorithm.use_kl_in_reward`, `algorithm.kl_ctrl.*`) or actor KL loss (`actor_rollout_ref.actor.use_kl_loss`, `kl_loss_coef`, `kl_loss_type`) according to the algorithm recipe.

## Backend Strategy Mismatches

- **Symptom**: Megatron-specific fields are ignored on FSDP or FSDP fields are ignored on Megatron.
  **Fix**: Set `model_engine=megatron` for Megatron commands and keep Megatron sizes under `.megatron.*`; keep FSDP offload/wrap fields under FSDP configs for FSDP/FSDP2.

- **Symptom**: TensorRT-LLM backend selected on unsupported accelerator.
  **Fix**: Use TensorRT-LLM only in compatible GPU environments; examples guard against `INFER_BACKEND=trtllm` on NPU.

- **Symptom**: NPU examples fail because GPU-specific backend options were retained.
  **Fix**: Use NPU-oriented overrides such as disabling torch compile when needed, using supported attention backend options, and setting trainer device/resource counts consistently.

## Distillation Sizing and Teacher Errors

- **Symptom**: distillation resource pool size mismatch.
  **Cause**: Sum of teacher `num_replicas * data_parallel_size * tensor_model_parallel_size * pipeline_model_parallel_size` does not match `distillation.n_gpus_per_node * distillation.nnodes`.
  **Fix**: Recompute the teacher world sizes and either change teacher replica/parallel sizes or change the teacher resource pool.

- **Symptom**: teacher inference max length validation fails.
  **Cause**: Teacher must score student prompt plus full response plus one generated token.
  **Fix**: Set teacher `inference.max_model_len >= data.max_prompt_length + data.max_response_length + 1`.

- **Symptom**: multi-teacher setup silently drops the default teacher.
  **Fix**: Add explicit names with `+distillation.teacher_models.teacher_model1...` and `+distillation.teacher_models.teacher_model2...`; do not mix the default `teacher_model` with added teacher keys when the intent is multiple teachers.

## Config Documentation and Generated YAML Checks

- **Symptom**: config documentation CI fails.
  **Fix**: For YAMLs covered by config-doc tests, every key line needs a preceding comment, no inline comments after fields, and blank lines between fields unless the next line is a deeper nested line.

- **Symptom**: generated trainer config is out of date.
  **Fix**: Regenerate flattened references with the repo maintenance script in a developer checkout, then inspect diffs. Do not make generated YAML the primary source of truth.

## Safe Validation Choices

- Prefer `python -m verl.trainer.main_ppo --help` or Hydra config printing for syntax exploration if dependencies are available.
- Prefer CPU unit tests for algorithm math (`tests/trainer/ppo/test_core_algos_on_cpu.py`) when validating logic without GPUs.
- Treat full example scripts such as large Qwen3 PPO/GRPO runs as GPU-expensive native candidates, not default verification commands.
