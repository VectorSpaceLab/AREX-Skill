# Training troubleshooting

Use this page when an EasyR1 training launch fails, a config linter warning is unclear, or a run starts but fails during Ray, FSDP, vLLM, rollout, reward, logging, save, or resume setup.

## First triage

1. Do not treat CPU lint success as training proof. Full training needs CUDA plus the EasyR1 runtime stack: Ray, vLLM, flash-attn, compatible PyTorch/CUDA, model assets, dataset assets, and enough GPU memory.
2. Rebuild the final command with the bundled command builder so quoting is visible:

```bash
python scripts/easyr1_command_builder.py /path/to/easyr1_config.yaml --override key=value --multiline
```

3. Run the static linter:

```bash
python scripts/easyr1_config_lint.py /path/to/easyr1_config.yaml --strict
```

4. If failure happens after Ray/vLLM starts, inspect the printed resolved config at the top of the training log and compare it with the intended YAML plus CLI overrides.

## Runtime dependency blockers

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: flash_attn` or FlashAttention import/build failure | Runtime does not contain FlashAttention 2 compatible with the active CUDA/PyTorch stack. | Use a full EasyR1 training image or install a matching prebuilt/source build in a CUDA toolkit environment. Actor model loading uses `attn_implementation="flash_attention_2"`. |
| `ModuleNotFoundError: vllm` or vLLM engine import failure | Static/API environment lacks full vLLM runtime. | Use a training runtime with vLLM installed and matched to PyTorch/CUDA. Static config checks do not require vLLM, but training does. |
| `CUDA_HOME`/`nvcc` build errors while installing GPU packages | The environment can import CUDA PyTorch but lacks a CUDA toolkit for source builds. | Prefer a prebuilt training image or install compatible wheels. Do not claim full training verification until flash-attn and vLLM are present. |
| Model or dataset download/auth errors | Remote model/dataset unavailable, gated, or blocked by network. | Use local/cache paths, authenticate the hub, set an approved mirror endpoint, or pre-download assets. |
| `RuntimeError: 0 active drivers ([]). There should only be one.` | Conflicting DeepSpeed installation in the environment. | Remove DeepSpeed from the training environment used for EasyR1. |

## CUDA and memory failures

### vLLM CuMem or CUDA OOM

Known symptom:

```text
RuntimeError: CUDA Error: out of memory at /workspace/csrc/cumem_allocator.cpp:62
```

Fixes to try, from least invasive to more invasive:

1. Reduce `worker.rollout.gpu_memory_utilization`.
2. Enable or keep `worker.actor.offload.offload_params=true`.
3. Reduce `data.rollout_batch_size`, `data.mini_rollout_batch_size`, `worker.rollout.n`, or validation batch size.
4. Reduce `data.max_prompt_length`, `data.max_response_length`, `data.max_pixels`, or `worker.rollout.limit_images` for VL runs.
5. Increase `worker.rollout.tensor_parallel_size` only if world size allows it and vLLM supports the target model/LoRA setup.
6. Use BF16 settings on supported GPUs: `worker.actor.fsdp.torch_dtype=bf16` and `worker.actor.optim.strategy=adamw_bf16`.
7. Use LoRA instead of full fine-tuning when acceptable.
8. Move to more GPUs or a smaller model.

### Image features and image tokens do not match

Known symptom:

```text
ValueError: Image features and image tokens do not match: tokens: 8192, features 9800
```

Fixes:

- Increase `data.max_prompt_length`.
- Reduce `data.max_pixels`.
- For multi-image data, set a bounded `worker.rollout.limit_images`.
- If the error depends on dataset formatting or image placeholders, route to `data-and-rewards`.

### vLLM max token limit

Symptom:

```text
ValueError: max_num_batched_tokens should be greater than prompt_length + response_length.
```

Fix:

```bash
worker.rollout.max_num_batched_tokens=<larger_than_data.max_prompt_length_plus_data.max_response_length>
```

For example, with `data.max_prompt_length=2048` and `data.max_response_length=20480`, set `worker.rollout.max_num_batched_tokens` above `22528`.

## Ray and distributed resource failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Total available GPUs ... is less than total desired GPUs ...` | Ray resource pool does not match `trainer.nnodes * trainer.n_gpus_per_node`. | Run `ray status`, start missing worker nodes, or reduce `trainer.nnodes` / `trainer.n_gpus_per_node`. |
| Training hangs before workers initialize | Ray cluster not started, wrong head/worker connection, or command launched on a worker instead of head. | Start Ray head, connect workers, verify `ray status`, launch `python -m verl.trainer.main` on the head node only. |
| `Tensor parallelism size should be less than world size.` | `worker.rollout.tensor_parallel_size` exceeds world size. | Set TP no larger than `trainer.nnodes * trainer.n_gpus_per_node`. |
| `rollout world size ... is not divisible by tp size ...` | Tensor parallel size does not divide worker world size. | Choose a TP divisor of total rollout GPUs. |
| Ray timeline not produced | Profiling not enabled or timeline path missing. | Set `RAY_PROFILING=1` and `trainer.ray_timeline=/path/to/timeline.json`. |

## Algorithm, clipping, and enum mistakes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Unknown advantage estimator` | `algorithm.adv_estimator` value not in EasyR1's estimator enum. | Use `gae`, `grpo`, `grpo_passk`, `reinforce_plus_plus`, `remax`, or `rloo`. DAPO is not a separate estimator; use GRPO-style estimator plus online filtering and clipping. |
| `Unknown KL penalty` | Invalid `algorithm.kl_penalty`. | Use `kl`, `abs`, `mse`, `low_var_kl`, or `full`. |
| `Unknown kl type` | Invalid `algorithm.kl_type`. | Use `fixed` or `adaptive`; adaptive also needs `kl_horizon > 0`. |
| `Unknown mode` for loss averaging | Invalid `worker.actor.loss_avg_mode` or `worker.critic.loss_avg_mode`. | Use `token` or `seq`. |
| `GRPO and RLOO algorithm need config.worker.rollout.n > 1` | Grouped estimator with only one rollout. | Set `worker.rollout.n` above 1. Apply the same rule for GRPO Pass@k. |
| GSPO run unstable or lint warning | `worker.actor.loss_type=gspo_token` without sequence averaging. | Use `worker.actor.loss_avg_mode=seq` unless there is a deliberate experiment reason. |
| CISPO run clipped unexpectedly | CISPO examples use much wider clipping. | Review `worker.actor.clip_ratio_low` and `worker.actor.clip_ratio_high`; distilled patterns use `0` and `4`. |
| SAPO behaves like default PPO | `worker.actor.loss_type` not set to `sapo`. | Set `worker.actor.loss_type=sapo`; tune `tau_positive` and `tau_negative` only after baseline run works. |

## Batch divisibility and FSDP setup failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Rollout batch size must be divisible by actor global batch size.` | `data.rollout_batch_size % worker.actor.global_batch_size != 0`. | Change one of the two batch sizes. |
| `Rollout batch size * rollout.n must be divisible by actor micro batch size for experience.` | Experience micro-batch does not divide generated rollout count. | Make `worker.actor.micro_batch_size_per_device_for_experience` divide `data.rollout_batch_size * worker.rollout.n`. |
| Critic batch divisibility errors | `algorithm.adv_estimator=gae` enables critic constraints. | Adjust critic global and micro batches, or use a non-critic estimator if intended. |
| `global batch size * ulysses size must be larger than num gpus` | Effective per-device batch is zero. | Increase global batch size or reduce GPU count/Ulysses size. |
| `global batch size per device must be divisible by the micro batch size` | Update micro-batch does not divide effective global batch per device. | Adjust `worker.actor.micro_batch_size_per_device_for_update` or global batch. |
| `cannot use FSDP's CPU offload when gradient accumulation is enabled` | FSDP CPU offload is incompatible with that worker's gradient accumulation shape. | Disable FSDP CPU offload or align global and micro update batch sizes so no accumulation is needed. |

## DAPO online filtering failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `No sample is kept after filtering. Please check your data.` | All average reward scores fall outside `(filter_low, filter_high)`. | Verify `algorithm.filter_key`, widen `filter_low`/`filter_high`, check reward function outputs, or inspect dataset difficulty. |
| `Generated too many. Please check your data.` | Online filtering cannot accumulate enough kept samples within `trainer.max_try_make_batch`. | Increase `max_try_make_batch`, widen filters, reduce `data.rollout_batch_size`, improve reward signal, or debug reward metrics. |
| Key error for reward metric | `algorithm.filter_key` does not match a reward metric. | Use a metric emitted by the reward function, such as `overall` or a reward-specific normalized accuracy key. |
| Long DAPO run exhausts memory | Very long response budget, high rollout count, or large batch. | Reduce `data.max_response_length`, `worker.rollout.n`, `data.mini_rollout_batch_size`, or GPU memory utilization; verify `max_num_batched_tokens`. |

Reward implementation details and score-key smoke tests belong to `data-and-rewards`.

## LoRA and VL-specific failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| LoRA config type error | `worker.actor.model.lora.target_modules` or `exclude_modules` is not a string. | Use strings such as `all-linear`, `q_proj,k_proj,v_proj,o_proj`, or `.*visual.*`. |
| vLLM LoRA fails for a VL model | LoRA applied to vision tower. | Set `worker.actor.model.lora.exclude_modules='.*visual.*'` for Qwen-VL-style models. |
| LoRA rollout fails after increasing tensor parallel size | vLLM LoRA support is sensitive to model/runtime and TP settings. | Start with `worker.rollout.tensor_parallel_size=1`; increase only after a full-runtime smoke passes. |
| Vision tower should not be trained | Full VL fine-tune is too expensive or undesired. | Use `worker.actor.model.freeze_vision_tower=true`; check FSDP behavior because this can set `use_orig_params`. |
| VLM with Ulysses fails | EasyR1 documents VLM incompatibility with Ulysses parallelism. | Use `worker.actor.ulysses_size=1` for VLMs unless the runtime has a verified fix. |

## Logging problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Hosted logger login error | `wandb`, `swanlab`, or `mlflow` selected without credentials/config. | Use `trainer.logger='["console","file"]'` until credentials are configured. |
| CLI logger override parsed incorrectly | Shell quoting broke the list. | Quote JSON-style lists: `trainer.logger='["console","wandb"]'`. |
| No generation samples logged | `trainer.val_generations_to_log=0` or validation disabled. | Set `trainer.val_freq`, keep validation enabled, and set `trainer.val_generations_to_log` above zero. |

## Save and resume problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Resume path rejected | `trainer.load_checkpoint_path` does not end in `global_step_*`. | Point to a specific global-step directory. |
| Expected auto-resume did not happen | `trainer.find_last_checkpoint=false`, save path changed, or tracker missing. | Set `find_last_checkpoint=True` and keep `trainer.save_checkpoint_path` stable across runs. |
| Optimizer state missing after resume | Prior run used `trainer.save_model_only=true`. | Use full checkpoints for resumable training; model-only saves are for lighter storage/export. |
| Want Hugging Face export after training | Training checkpoint format is not the final HF layout. | Use `checkpoint-export` after training; do not handle merge/export in this sub-skill. |

## Validation-only and short smoke confusion

- `trainer.val_only=True` still initializes enough runtime to validate with the configured reward function and data; it is not a CPU-only static test.
- `trainer.max_steps=1` still starts Ray/vLLM workers and uses CUDA.
- The bundled linter and command builder are the CPU-safe checks for this sub-skill.

## When to route elsewhere

- Missing dataset columns, prompt template syntax, image/video path handling, reward function import, reward return schema, Android GUI service/device setup: route to `data-and-rewards`.
- `DataProto` union/split/repeat/pad errors or dynamic sequence-length balancing internals: route to `core-apis`.
- Actor checkpoint shard layout, Hugging Face conversion, LoRA adapter merge, upload, or generation config preservation: route to `checkpoint-export`.
