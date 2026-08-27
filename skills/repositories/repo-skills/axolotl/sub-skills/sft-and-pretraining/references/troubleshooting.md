# SFT and Pretraining Troubleshooting

Use this guide for Axolotl SFT and continual pretraining runs. Route RL reward instability, vLLM synchronization, KL, or policy metrics to the RL/rewards sub-skill.

## Loss Plateau or No Learning

Symptoms:

- `train/loss` stays flat from the first steps.
- `grad_norm` is near zero.
- Eval loss does not improve.

Checks:

1. Run `axolotl preprocess config.yaml --debug` and inspect whether target tokens are labeled and prompt/user tokens are masked as intended.
2. For chat data, confirm the dataset really matches `type: chat_template` and the tokenizer has a chat template or an explicit template/fallback is configured.
3. Confirm `train_on_inputs` is intentional; SFT usually masks inputs, while completion/pretraining learns all tokens.
4. Increase LR only after data/masking is proven correct. Typical starting ranges are lower for full fine-tune than for LoRA/QLoRA.
5. Check that adapter fields actually train parameters; unexpected frozen weights or bad target modules belongs with model/adapters guidance.

## Loss Spikes, NaN, or Inf

Symptoms:

- Loss jumps by multiple factors, becomes `nan`, or `grad_norm` spikes above normal ranges.
- Failure happens only on some batches.

Stabilization order:

1. Lower `learning_rate` by 2x to 5x and increase warmup (`warmup_ratio` or `warmup_steps`).
2. Set `max_grad_norm: 1.0` if gradient clipping is absent.
3. Temporarily disable `sample_packing` to isolate a bad or overlong sample.
4. Run `axolotl preprocess config.yaml --debug` and inspect empty strings, empty assistant turns, unexpected token IDs, and very long rows.
5. Use `bf16: auto` rather than forcing a precision mode the hardware may not handle well.
6. Reduce to one GPU and one micro-batch for diagnosis before debugging distributed-specific behavior.

Known SFT/pretraining-specific cautions:

- `sample_packing` with unsupported attention behavior can produce invalid loss behavior; prefer `attn_implementation: flash_attention_2` for packed recipes.
- Missing or incorrect pad tokens can create masking and infinite-loss issues. Many Llama-style recipes set a known end-of-text token as `special_tokens.pad_token`.
- FP8 and custom kernels are advanced paths; route kernel-specific debugging to model/performance guidance unless the user only needs a conservative fallback.

## OOM During Preprocess or Training

Fast reductions:

1. Set `micro_batch_size: 1`.
2. Increase `gradient_accumulation_steps` if the effective batch should stay similar.
3. Reduce `sequence_len`.
4. Enable `gradient_checkpointing: true`.
5. Use QLoRA (`adapter: qlora`, `load_in_4bit: true`) when adapter training is acceptable.
6. Use `attn_implementation: flash_attention_2` for long packed sequences when the environment supports it.
7. For very large models or full fine-tunes, route launch/sharding choices to distributed/performance guidance.

If OOM appears during preprocessing, check `dataset_num_proc`, packing buffer sizes, `sequence_len`, and whether the dataset is being fully materialized. For massive corpora, switch from non-streaming `type: completion` to streaming `pretraining_dataset` if it matches the training goal.

## Batch Size Confusion

Axolotl’s effective batch is:

```text
micro_batch_size * gradient_accumulation_steps * number_of_gpus
```

Problems and fixes:

- If the user set `batch_size`, prefer converting the intent into `micro_batch_size` plus `gradient_accumulation_steps`.
- If loss becomes noisy after reducing `micro_batch_size`, increase accumulation or lower LR.
- If training is slow but stable, do not immediately increase `micro_batch_size`; consider packing, preprocessing reuse, or distributed/performance guidance.

## Tokenizer or Chat Template Mismatch

Symptoms:

- Preprocess errors about chat templates.
- Debug output shows wrong roles, missing assistant labels, or all labels masked.
- Inference after training uses unexpected prompt formatting.

Checks:

1. For `type: chat_template`, ensure records use the expected message structure or route custom mapping to data/configs.
2. If relying on tokenizer defaults, confirm the tokenizer includes a chat template. Otherwise set a known Axolotl `chat_template` or a custom `chat_template_jinja`.
3. Keep the same config for preprocess, train, inference, and merge so the saved tokenizer/template remains consistent.
4. Regenerate prepared data after changing tokenizer, chat template, dataset format, `sequence_len`, packing, or `train_on_inputs`.

## Checkpoint and Resume Confusion

Common issues:

- `resume_from_checkpoint` points to the wrong run or a non-checkpoint directory.
- `auto_resume_from_checkpoints` picks the latest numeric checkpoint under a reused `output_dir`.
- Dynamic or interrupted saves contain model weights but not optimizer state.
- FSDP/optimizer state saving warnings mean a checkpoint may not support full resume.

Recommended triage:

1. Use a fresh `output_dir` for a different model, dataset, or adapter mode.
2. Prefer explicit `resume_from_checkpoint: ./outputs/run/checkpoint-N` when multiple run attempts share a parent directory.
3. Use `auto_resume_from_checkpoints: true` only when continuing the same run and the `output_dir` contains only compatible checkpoints.
4. For reliable resume, use scheduled or dynamic checkpoints rather than relying only on `Ctrl+C` graceful model save.
5. If optimizer/scheduler state was not saved, resume may restart optimizer dynamics even if weights load.

## `dataset_prepared_path` Reuse Problems

Symptoms:

- Training appears to ignore recent dataset/template changes.
- Label masks look stale.
- Sequence lengths or packing behavior do not match the current YAML.

Fix:

- Delete or change `dataset_prepared_path` and rerun `axolotl preprocess config.yaml`.
- Treat prepared data as tied to the model/tokenizer, dataset content, dataset type, prompt strategy, sequence length, packing, and masking settings.
- Do not share one prepared path between unrelated experiments.

## Sample Packing and Length Problems

Symptoms:

- OOM after enabling packing.
- Eval errors only when packed eval is enabled.
- 0.0 loss or invalid attention behavior.
- Slow startup while lengths are computed and packed.

Fixes:

1. Lower `sequence_len` and set `pad_to_sequence_len: true`.
2. Use `attn_implementation: flash_attention_2` when available.
3. Set `eval_sample_packing: false` if eval callbacks conflict with packed evaluation.
4. For streaming, lower `streaming_multipack_buffer_size` if memory pressure appears.
5. For pretraining, set `pretrain_multipack_attn: true` when packed documents should not attend to one another.

## Model Download, Network, and Local Path Errors

Axolotl may resolve `base_model`, tokenizer, and datasets from Hugging Face Hub, local files, S3, GCS, or other configured sources depending on the YAML and environment.

Before blaming Axolotl config logic:

- Check whether the runtime environment has network access and required credentials.
- For local paths, check relative paths from the command’s working directory.
- For private Hub models/datasets, confirm authentication is available outside the skill content.
- Avoid putting machine-specific absolute paths into reusable configs unless the user explicitly needs a local-only run.

## Conservative Recovery Config

When the user needs a safer single-GPU diagnostic run, suggest a temporary variant:

```yaml
micro_batch_size: 1
gradient_accumulation_steps: 8
sequence_len: 1024
sample_packing: false
max_steps: 20
logging_steps: 1
bf16: auto
gradient_checkpointing: true
```

Run `axolotl preprocess config.yaml --debug` first, then a short `axolotl train config.yaml` only if the user is ready to execute a model-loading/training command in their environment.
