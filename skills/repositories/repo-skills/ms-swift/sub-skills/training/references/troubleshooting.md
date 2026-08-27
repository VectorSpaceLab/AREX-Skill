# Training Troubleshooting

Use this guide before changing model code. Most ms-swift training failures come from source/download mismatch, missing optional dependencies, memory pressure, incompatible distributed flags, or checkpoint semantics.

## Model and Dataset Download Source

Symptoms:

- Model or dataset cannot be found.
- A run unexpectedly contacts ModelScope or HuggingFace.
- Offline machines fail during model checks before training begins.

Actions:

- Decide source explicitly. Use `--use_hf true` for HuggingFace behavior; default/false uses ModelScope behavior.
- For international ModelScope access, set `MODELSCOPE_DOMAIN=www.modelscope.ai`.
- For offline runs, pass local model and dataset paths, set offline environment variables such as `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` when using HuggingFace tooling, and add `--check_model false` for trusted local model paths.
- Keep datasets local for offline training; open-source datasets can be cloned ahead of time and passed by local path.
- If a config file has `ENV`, remember the current shell environment wins when a variable is already set.

## Missing Optional Dependencies

Symptoms:

- `deepspeed` import/version errors.
- Training-loop evaluation errors after enabling EvalScope.
- Metric/logging imports such as `jieba`, `wandb`, or `swanlab` fail.

Actions:

- Install DeepSpeed only for DeepSpeed runs: `pip install deepspeed -U`.
- Install EvalScope only when using `--eval_use_evalscope true`: `pip install ms-swift[eval] -U` or an equivalent environment with `evalscope`.
- Keep optional Megatron-specific troubleshooting in the distributed/RL sub-skill unless the user is using plain `swift sft` or `swift pt`.
- If a ReFT run fails with DeepSpeed or gradient checkpointing, simplify first: disable ReFT-specific features or DeepSpeed and retry a minimal command.

## CUDA, NPU, and Device Selection

Symptoms:

- Training sees the wrong GPU count.
- A single-GPU run unexpectedly launches distributed training.
- NPU/GPU runtime libraries are missing or mismatched.

Actions:

- Use `CUDA_VISIBLE_DEVICES=0` for a single selected GPU.
- Unset `NPROC_PER_NODE` and `NNODES` for non-distributed runs; setting either causes the top-level launcher to use `torch.distributed.run` for training routes.
- Use `NPROC_PER_NODE=<gpu_count>` for DDP/DeepSpeed/FSDP launch.
- For NPU environments, verify the PyTorch/NPU runtime pairing outside ms-swift before debugging training arguments.
- Avoid mixing `device_map` simple model parallelism with DeepSpeed or FSDP2 in this training path.

## CUDA OOM and Slow Training

Symptoms:

- CUDA out of memory during load, preprocessing, first step, evaluation, or checkpointing.
- Multimodal runs OOM on high-resolution images/video.
- Training is unexpectedly slow after enabling memory-saving options.

Actions:

1. Reduce `--max_length`.
2. Reduce `--per_device_train_batch_size`; increase `--gradient_accumulation_steps` if effective batch size matters.
3. For multimodal models, reduce `MAX_PIXELS` and `VIDEO_MAX_PIXELS`; keep values compatible with model recommendations, often multiples of 28×28 for Qwen-VL-style models.
4. Keep `--gradient_checkpointing true`; expect slower training because memory is traded for recomputation.
5. Use LoRA or QLoRA instead of full tuning when acceptable.
6. Use `--packing true` or `--padding_free true` only with `--attn_impl flash_attn` or another supported flash attention implementation.
7. Try DeepSpeed ZeRO2/ZeRO3 or FSDP2 for large full-parameter runs, but do not combine them.
8. For fragmentation-sensitive runs, try `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

## Packing and Padding-free Errors

Symptoms:

- Error says packing or padding-free requires a flash attention implementation.
- Packed training changes step counts or validation cadence.

Actions:

- Add a supported attention implementation such as `--attn_impl flash_attn`.
- Install the corresponding flash-attention dependency for the environment and hardware.
- Adjust learning rate, gradient accumulation, and save/eval cadence after enabling packing because samples are combined and the effective number of training examples changes.
- If the user only wants lower memory without preprocessing overhead, prefer `padding_free`; if they want more stable utilization and can pay preprocessing cost, prefer `packing`.

## DDP Gradient Checkpointing Reducer Error

Symptom:

- `RuntimeError: Expected to mark a variable ready only once.`

Actions:

- Add `--gradient_checkpointing_kwargs '{"use_reentrant": false}'` for DDP without DeepSpeed/FSDP.
- In YAML/JSON configs, write it as a dictionary so ms-swift converts it to a JSON argument string.
- Alternatively use DeepSpeed if that is acceptable and installed.

## DeepSpeed Issues

Symptoms:

- DeepSpeed import fails.
- Error says DeepSpeed is not compatible with `device_map`.
- ZeRO++ produces `grad_norm` NaN.

Actions:

- Install the optional dependency only when needed: `pip install deepspeed -U`.
- Remove `device_map` when using DeepSpeed.
- Use built-in presets first: `zero2`, `zero3`, `zero2_offload`, or `zero3_offload`.
- If `zero_hpz_partition_size` causes `grad_norm` NaN, try `--torch_dtype float16`.
- `deepspeed_autotp_size` requires a DeepSpeed zero0/zero1/zero2 config and full-parameter fine-tuning.

## FSDP2 Issues

Symptoms:

- Error says FSDP2 is incompatible with DeepSpeed or `device_map`.
- Warning recommends activation checkpointing instead of gradient checkpointing.
- Save-only-model fails with sharded state dict.

Actions:

- Do not combine `--fsdp fsdp2` with `--deepspeed`.
- Remove `device_map` for FSDP2.
- Prefer `activation_checkpointing` in `fsdp_config` instead of ordinary `gradient_checkpointing`.
- Avoid `save_only_model true` with a sharded state dict; use a full state dict config or save full training state.

## LoRA, QLoRA, Merge, and vLLM Acceleration

Symptoms:

- User wants vLLM/SGLang/LMDeploy acceleration after QLoRA.
- Merge/export fails for a quantized adapter workflow.
- Inference command points `--model` at an adapter checkpoint.

Actions:

- For LoRA checkpoints, use `--adapters CHECKPOINT_DIR` during inference/deployment, with `--model BASE_MODEL` when the checkpoint args do not fully specify the base.
- For full fine-tuning checkpoints, use `--model CHECKPOINT_DIR`.
- If accelerated inference needs merged weights, prefer LoRA or full-parameter training and then route merge/export/quantization to `export-evaluation`.
- Do not promise LoRA merge for QLoRA-trained adapters. If acceleration is a requirement, recommend retraining with LoRA/full or using a supported export path after a compatible merge.
- Ensure vLLM LoRA rank limits are at least the training `lora_rank` when serving adapters directly in a supported path.

## Base-to-Chat Template Problems

Symptoms:

- A base model fine-tuned for chat does not stop correctly.
- Generated text includes special chat tokens or malformed dialogue markers.
- Loss appears to target the wrong token regions.

Actions:

- For continued pre-training, use `swift pt` or explicitly set `--use_chat_template false --loss_scale all`.
- For SFT from a base model to chat behavior, try `--template default` to avoid exposing the model to unfamiliar chat-control tokens.
- For instruction-tuned chat models, keep the model’s expected template unless there is clear evidence it is wrong.
- Keep dataset message schema debugging in `data-model-customization`.

## Streaming, Lazy Tokenization, and Cached Dataset Problems

Symptoms:

- Streaming run never stops or cannot compute epochs.
- Cached dataset behaves differently from raw dataset training.
- Multimodal preprocessing consumes too much memory before training.

Actions:

- Set `--max_steps` for `--streaming true`; streaming datasets do not have a finite length.
- For cached datasets produced with split truncation, reuse the same `max_length` and `truncation_strategy` during training.
- Use `--lazy_tokenize true` for multimodal or memory-constrained preprocessing.
- If image augmentation is required, lazy tokenization or streaming must be enabled so encoding happens during training.

## Checkpoint Resume Surprises

Symptoms:

- Resumed run repeats or skips unexpected data.
- Optimizer state is not restored.
- Adapter weights load but training state does not.

Actions:

- Use `--resume_from_checkpoint CHECKPOINT_DIR` to restore weights, optimizer state, RNG, and progress.
- Use `--resume_only_model true` only when you intentionally want model weights without optimizer/RNG state.
- Use `--adapters CHECKPOINT_DIR` to load adapter weights only; it is not equivalent to resuming training.
- Keep the original training parameters unchanged when doing a true resume.
- If automation needs stable latest/best paths, enable `--create_checkpoint_symlink true`.
