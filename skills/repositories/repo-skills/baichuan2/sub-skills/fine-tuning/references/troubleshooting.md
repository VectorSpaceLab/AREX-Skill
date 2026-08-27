# Fine-Tuning Troubleshooting

This troubleshooting guide is limited to supervised training, DeepSpeed, LoRA, data validation, and post-training loadability.

## Missing DeepSpeed

Symptoms:

- `deepspeed: command not found`
- `ModuleNotFoundError: No module named 'deepspeed'`
- DeepSpeed launcher starts but exits before parsing trainer arguments

Actions:

1. Install DeepSpeed in the same Python environment used by the launcher: `python -m pip install deepspeed`.
2. Confirm `which deepspeed` and `python -c "import deepspeed"` resolve to that environment.
3. Run `deepspeed --help | head -n 20`.
4. If optional compiled-op warnings appear, continue only if imports, CLI help, CUDA smoke, and a tiny launch pass.

## Missing LoRA / PEFT dependencies

Symptoms:

- `ModuleNotFoundError: No module named 'peft'`
- `--use_lora True` fails during model wrapping
- Output directory lacks expected adapter files

Actions:

1. Install PEFT: `python -m pip install peft`.
2. Confirm `python -c "import peft; print(peft.__version__)"`.
3. Keep `--lora_target_modules W_pack` for standard Baichuan2 attention unless the model architecture has been changed.
4. Remember that LoRA output should be loaded with `peft.AutoPeftModelForCausalLM`, not plain `AutoModelForCausalLM` unless adapters have been merged.

## Data schema mismatches

Symptoms:

- `KeyError: 'conversations'`, `KeyError: 'from'`, or `KeyError: 'value'`
- training runs but loss is nonsensical because roles are wrong
- all or most samples are truncated

Actions:

1. Run `scripts/validate_training_data.py --data_path ...`.
2. Convert OpenAI-style `messages[].role/content` data to `conversations[].from/value`.
3. Normalize `user` to `human`; use `gpt` or `assistant` for assistant turns.
4. Review empty messages; reject them with `--no-allow_empty_values` unless intentionally modeling empty answers.
5. Ensure conversations contain assistant target text, preferably ending with an assistant turn.
6. Use `--require_alternating` when your dataset is expected to strictly alternate human and assistant turns.
7. If token truncation is high, increase `model_max_length` only if VRAM allows, or filter/chunk long samples.

## Hostfile formatting errors

Symptoms:

- DeepSpeed reports bad hostfile entries
- launcher cannot SSH to nodes
- job starts with fewer ranks than expected
- NCCL hangs immediately in multi-node mode

Actions:

1. Use one line per node: `hostname slots=N`.
2. Do not add commas, JSON syntax, comments after entries, or GPU IDs in the hostfile.
3. Verify every hostname resolves from the launch node.
4. Verify SSH is non-interactive if using DeepSpeed's standard launcher.
5. Ensure `slots` does not exceed visible GPUs on that node.
6. Keep package versions, CUDA access, model cache, and data paths consistent across nodes.

## VRAM and batch-size failures

Symptoms:

- `CUDA out of memory`
- OOM during model load or first backward pass
- OOM only during checkpoint save

Actions:

1. Reduce `--per_device_train_batch_size` first.
2. Increase `--gradient_accumulation_steps` to preserve effective batch size.
3. Keep `--model_max_length 512` until a smaller run succeeds.
4. Keep `--gradient_checkpointing True` for memory reduction.
5. Use `--use_lora True` when full-parameter fine-tuning is too expensive.
6. Check output filesystem space for ZeRO-3 gathered checkpoints.

## bf16, tf32, and gradient-checkpointing incompatibilities

Symptoms:

- bf16 unsupported errors
- numerical instability after changing precision flags
- warnings about `use_cache=True` with gradient checkpointing
- unexpected slowdown or matmul precision warnings

Actions:

1. Use `--bf16 True` only on hardware and torch builds that support bf16. A100-class GPUs do.
2. If bf16 fails, retry with `--bf16 False`; do not mix unsupported precision assumptions across nodes.
3. `--tf32 True` is a performance flag for NVIDIA Ampere+ matmul paths. Disable it if exact reproducibility or hardware support is a concern.
4. With `--gradient_checkpointing True`, set or allow the trainer to set `model.config.use_cache=False` during training.
5. If failures occur only on some nodes, compare GPU model, driver, CUDA runtime, and torch build.

## DeepSpeed ZeRO-3 save/load problems

Symptoms:

- Saved full model cannot be loaded with `from_pretrained`
- checkpoint directories contain only ZeRO partition shards
- final save hangs or uses much more memory than training steps

Actions:

1. Keep `stage3_gather_16bit_weights_on_model_save: true` for direct full-model loading.
2. Confirm `trainer.save_model(output_dir=...)` completed after `trainer.train()`.
3. For interrupted runs, inspect the latest checkpoint and resume intentionally rather than assuming final output is complete.
4. For LoRA runs, use PEFT loading; direct full-model loading is not the expected path unless you have merged adapters.

## `use_lora` / PEFT behavior

The trainer wraps the base model only when `--use_lora True` is passed. The default PEFT configuration is:

- task type: causal language modeling;
- target module: `W_pack`;
- rank: `1`;
- alpha: `32`;
- dropout: `0.1`;
- inference mode: `False`.

If no trainable parameters are printed or training appears to update nothing:

1. verify `--use_lora True` was parsed;
2. verify the target module name exists in the loaded model;
3. lower memory pressure before increasing LoRA rank;
4. do not expect LoRA output to look like a full checkpoint unless adapters are merged.
