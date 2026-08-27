# Training Options for SFT and Pretraining

## Minimal Config Anatomy

Every SFT or pretraining recipe needs these decisions:

```yaml
base_model: NousResearch/Llama-3.2-1B
output_dir: ./outputs/my-run
sequence_len: 2048
micro_batch_size: 1
gradient_accumulation_steps: 4
num_epochs: 1
learning_rate: 0.0002
optimizer: adamw_8bit
lr_scheduler: cosine
bf16: auto
```

Then add exactly one data family:

```yaml
datasets:
  - path: ./chat.jsonl
    type: chat_template
```

or:

```yaml
pretraining_dataset:
  - path: ./corpus.jsonl
    type: pretrain
    text_column: text
max_steps: 1000
```

`max_steps` takes precedence over `num_epochs` when both are set. Use it for streaming datasets and bounded smoke runs.

## LoRA, QLoRA, or Full Fine-Tune

| Mode | Use when | Core fields | Starting knobs |
|---|---|---|---|
| LoRA | Common SFT baseline with moderate VRAM and adapter output | `adapter: lora`; optionally `load_in_8bit: true` | `lora_r: 16`, `lora_alpha: 32`, `lora_dropout: 0.05`, LR around `1e-4` to `3e-4`. |
| QLoRA | Need lower memory via 4-bit base model loading | `adapter: qlora`, `load_in_4bit: true` | `lora_r: 16` to `64`, `gradient_accumulation_steps` often higher, optimizer such as `adamw_bnb_8bit`. |
| Full fine-tune | Need to update all model weights and hardware allows it | Omit `adapter`, `load_in_4bit`, and `load_in_8bit` | Lower LR around `1e-5` to `5e-5`, small `micro_batch_size`, often distributed launch. |

Important adapter constraints:

- `load_in_8bit` or `load_in_4bit` is for adapter-style training, not full fine-tuning.
- QLoRA training requires `load_in_4bit: true` and rejects `load_in_8bit`.
- Do not claim that LoRA target modules are universal. If the user needs architecture-specific targets, route to model/adapters guidance.
- LoRA kernel options such as `lora_mlp_kernel`, `lora_qkv_kernel`, and `lora_o_kernel` are SFT-only optimization flags with model/backend constraints; treat them as advanced and route deeper compatibility questions to model-loading/adapters or performance guidance.

## Dataset Types in This Sub-Skill

| `type` | Best fit | Main caution |
|---|---|---|
| `chat_template` | Chat/message records, including OpenAI-style role/content messages | Confirm tokenizer chat template or set a known Axolotl template/fallback. |
| `alpaca` | `instruction`, optional `input`, and `output` rows | Use only when columns match the Alpaca contract. |
| `input_output` | Explicit prompt/response pairs | Dataset schema details belong in data/configs. |
| `completion` | Raw text where all tokens should be learned | This is pretraining-style, not prompt/response masking. |
| `pretrain` under `pretraining_dataset` | Streaming pretraining | Requires `max_steps`; not the same as supervised SFT. |

For SFT, `train_on_inputs` defaults to false in the training schema, so prompt tokens are generally masked unless configured otherwise. For completion/pretraining data, the whole text is the training target.

## Batch Size and Accumulation

Effective batch size is:

```text
micro_batch_size * gradient_accumulation_steps * number_of_gpus
```

Guidance:

- Reduce `micro_batch_size` first for OOM; increase `gradient_accumulation_steps` to keep the effective batch comparable.
- Avoid setting `batch_size` directly unless an existing config already does so; Axolotl warns that gradient accumulation is preferred.
- For first one-GPU QLoRA tests, `micro_batch_size: 1` or `2` plus `gradient_accumulation_steps: 4` to `16` is a safer starting range.
- Large effective batches can change learning dynamics; if loss plateaus or spikes, revisit LR and warmup, not only memory knobs.

## Sample Packing

`sample_packing: true` packs shorter examples into fixed-length sequences to improve utilization. Pair it with:

```yaml
sample_packing: true
eval_sample_packing: true
pad_to_sequence_len: true
attn_implementation: flash_attention_2
```

Cautions:

- Packing increases the importance of a reasonable `sequence_len`; too-large values can cause OOM or slow preprocessing.
- Some validation paths warn when `eval_sample_packing` is inferred; make it explicit for clarity.
- If `eval_table_size`, causal LM eval, or special eval callbacks conflict with packed eval, set `eval_sample_packing: false` and review `remove_unused_columns` if needed.
- For streaming pretraining, use `pretrain_multipack_attn: true` when packed examples must not attend across document boundaries.

## Output, Prepared Data, and Checkpoint Fields

Core fields:

```yaml
output_dir: ./outputs/my-run
dataset_prepared_path: ./prepared/my-run
save_strategy: steps
save_steps: 250
save_total_limit: 3
resume_from_checkpoint:
auto_resume_from_checkpoints: false
```

Use `dataset_prepared_path` when:

- Preprocessing is expensive and should be reused.
- You want a stable handoff between `axolotl preprocess` and `axolotl train`.
- You are iterating on training hyperparameters without changing tokenizer, dataset, or prompt formatting.

Do not reuse `dataset_prepared_path` blindly after changing `base_model`, tokenizer/chat template, dataset path/type, `sequence_len`, packing, or masking settings; regenerate it to avoid stale tokenization or label masks.

Use `save_steps` or `saves_per_epoch`, not both. If `save_steps` is set, make sure `save_strategy` is compatible with step checkpointing or omit `save_strategy` when Axolotl can infer it.

## Validation Checklist

Before recommending `axolotl train`:

- Confirm there is no RL field for this sub-skill’s workflow.
- Confirm `datasets` or `pretraining_dataset` exists, but do not mix workflows unless a known Axolotl pattern requires it.
- Confirm `base_model`, `output_dir`, `learning_rate`, batch fields, precision, and sequence length are intentional.
- Confirm QLoRA has `adapter: qlora` and `load_in_4bit: true`.
- Confirm full fine-tune does not use load-in-4bit/8bit adapter fields.
- Confirm streaming/pretraining uses `max_steps`.
- Confirm the user understands remote model/dataset paths may require network and credentials at runtime.
- Prefer `axolotl preprocess config.yaml --debug` before expensive runs when there is any uncertainty about labels, chat templates, empty samples, or packing.
