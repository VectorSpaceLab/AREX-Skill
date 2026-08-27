# Core Training Troubleshooting

Use this matrix to diagnose Unsloth Core planning, import, backend, model-loading, LoRA, trainer, and data issues before running expensive training.

## Import Order Warning

Symptom:

- Warning says Unsloth should be imported before `trl`, `transformers`, or `peft`.

Likely cause:

- A script imported one of those libraries before `import unsloth`, preventing early patching.

Recovery:

- Move `import unsloth` to the top of the entrypoint before importing training libraries.
- Restart the Python process or notebook kernel; already-imported modules remain patched/initialized in the current process.
- Re-run `scripts/inspect_unsloth_core.py` from a fresh process to confirm imports.

## Missing `torch`, `numpy`, `unsloth_zoo`, `triton`, Or `bitsandbytes`

Symptoms:

- `ImportError: Unsloth: Pytorch is not installed`.
- `ImportError: Please install unsloth_zoo`.
- `bitsandbytes is not installed - 4bit QLoRA unallowed`.
- Import fails before signatures can be inspected.

Likely cause:

- Core training dependencies are incomplete or installed for a different backend/Python.

Recovery:

- Reinstall Unsloth with public package instructions appropriate for the target backend.
- If `bitsandbytes` is missing, switch the recipe to `load_in_4bit=False` / `load_in_8bit=False` for 16-bit or full finetuning until the dependency is available.
- If `torch` is intentionally omitted, do not plan Core training; limit work to config/data preparation or Studio non-training capabilities.

## CUDA `ldconfig` Warning

Symptom:

- Warning says CUDA is not linked properly and suggests `ldconfig` commands.

Likely cause:

- CUDA libraries are present but not discoverable by bitsandbytes/triton.

Recovery:

- Ask the user before running privileged system commands.
- Have the user run the suggested `sudo ldconfig` command for their CUDA library directory, then restart Python.
- For planning-only work, generate a non-executed recipe and note that 4-bit training remains blocked until CUDA linking is fixed.

## GPU Path Versus MLX Path

Symptoms:

- `unsloth.DEVICE_TYPE` is `mlx` on Apple Silicon.
- `FastSentenceTransformer` raises not implemented on MLX.
- `UnslothVisionDataCollator` raises not implemented on MLX.
- A GPU host unexpectedly follows Apple/MLX behavior.

Likely cause:

- Unsloth selects MLX only on Darwin arm64 with MLX available unless `UNSLOTH_FORCE_GPU_PATH=1` is set.

Recovery:

- On Apple Silicon, use MLX-compatible Core paths and avoid unsupported sentence-transformer/vision collator flows.
- On GPU hosts, set `UNSLOTH_FORCE_GPU_PATH=1` before importing Unsloth only when MLX misdetection is suspected.
- Keep backend-specific notes out of public configs; make them runtime environment instructions.

## Tokenizer Or Chat Template Mapping Fails

Symptoms:

- Template rendering errors on role alternation.
- `KeyError` for unknown chat template names.
- Missing role/content fields.
- Outputs lack EOS/stop tokens or assistant labels.

Likely cause:

- Dataset fields do not match `mapping`, role aliases are incomplete, or the selected template is wrong for the model family.

Recovery:

- Validate a tiny JSONL sample with `scripts/validate_training_config.py --data sample.jsonl`.
- For OpenAI-style rows, use `messages`, `role`, and `content`.
- For ShareGPT-style rows, use `conversations`, `from`, and `value`, then run `standardize_sharegpt`.
- Use `get_chat_template(tokenizer, chat_template="chatml", mapping=...)` for generic chat data, or a model-family template such as `llama-3`, `gemma`, `gemma4`, `mistral`, or `phi-3` when required.
- Keep `map_eos_token=True` unless the recipe explicitly manages EOS.

## Dataset Field Errors

Symptoms:

- `SFTTrainer` cannot find `dataset_text_field`.
- Formatting function returns empty text.
- `RawTextDataLoader` rejects empty files, `chunk_size`, or `stride`.
- Vision collator raises missing video file errors.

Likely cause:

- Config/data mismatch, tiny sample not representative, or invalid raw-text chunking parameters.

Recovery:

- For text SFT, ensure the transformed dataset has a `text` column if using `dataset_text_field="text"`.
- If using a formatting function, do not rely on a nonexistent text column.
- For raw text, set `chunk_size > 0` and `0 <= stride < chunk_size`.
- For VLM data, verify every local path before trainer creation; missing videos are intentionally surfaced by the collator.

## LoRA And Full-Finetuning Mismatch

Symptoms:

- Loader prints that full finetuning disables LoRA/QLoRA.
- Quantization-combination runtime error.
- `get_peft_model` has no effect.

Likely cause:

- The recipe mixes `full_finetuning=True` with `load_in_4bit`, `load_in_8bit`, `load_in_16bit`, `load_in_fp8`, or an adapter setup.

Recovery:

- QLoRA: keep `full_finetuning=False`, `load_in_4bit=True`, then call `get_peft_model`.
- 8-bit LoRA: set `load_in_4bit=False`, `load_in_8bit=True`, and do not set other quantization flags.
- Full finetuning: set quantization flags false and skip adapter creation.
- For LoftQ init, reload without `load_in_4bit=True`.

## LoRA Target Or Module Errors

Symptoms:

- Custom module warning says Unsloth has not optimized the target.
- `modules_to_save` rejects a module name.
- Vision LoRA complains about fast inference or unsupported VLM LoRA.
- MoE expert parameters are not discovered.

Likely cause:

- Target modules are outside the optimized default set, embedding/head modules are misplaced, or vision/text filters do not match the target architecture.

Recovery:

- Text default target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- Use `modules_to_save` only for `embed_tokens` and `lm_head`.
- For VLMs, use `finetune_vision_layers`, `finetune_language_layers`, `finetune_attention_modules`, and `finetune_mlp_modules` instead of hand-writing broad regexes.
- For MoE, use broad MLP projection patterns when expert `target_parameters` should be auto-discovered.

## `trust_remote_code`, Tokens, And Downloads

Symptoms:

- Model config cannot be loaded without remote code.
- Gated/private model access fails.
- Planning unexpectedly downloads model weights.

Likely cause:

- The target model requires custom code or authentication, or the agent ran loader code instead of planning.

Recovery:

- Keep `trust_remote_code=False` by default and ask the user before enabling it.
- Accept tokens through environment or runtime secrets, not checked-in config.
- Do not execute `from_pretrained` during planning unless the user explicitly approves downloads and the runtime is prepared.
- Use `scripts/inspect_unsloth_core.py` for signatures because it imports APIs but does not load models.

## Context Length And VRAM Pressure

Symptoms:

- Out-of-memory during load or training.
- Training is very slow or fails after increasing `max_seq_length`.
- Long-context recipe cannot fit batch size.

Likely cause:

- Context length, model size, full finetuning, precision, and batch settings exceed the backend memory budget.

Recovery:

- Prefer QLoRA with `load_in_4bit=True` before full finetuning on limited VRAM.
- Lower `max_seq_length`, `per_device_train_batch_size`, or enable/increase `gradient_accumulation_steps`.
- Keep `use_gradient_checkpointing="unsloth"` for decoder QLoRA recipes unless there is a known incompatible model path.
- Use sample packing only for text SFT when there is no custom collator or processor-based model.
- For VLMs, reduce image/video resolution and disable vision-layer adapters when the user only needs text behavior adaptation.

## Stray Forward Before Training

Symptom:

- Warning mentions manual forward/backward before `trainer.train()` and reset of compile cache.

Likely cause:

- A grad-enabled probe ran before training and could poison compiled backward graphs.

Recovery:

- Avoid manual forward/backward checks before `trainer.train()`.
- Use `torch.no_grad()` for inspection-only probes.
- Restart the process if repeated compile-cache warnings persist during recipe debugging.
