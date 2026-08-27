# SFT and Pretraining Workflows

## Decide the Training Family

Use the Axolotl config shape to classify the run before editing fields:

| Goal | Config pattern | Notes |
|---|---|---|
| Supervised fine-tuning | `datasets:` with a supervised `type` such as `chat_template`, `alpaca`, `input_output`, or a custom strategy | Default Axolotl training when `rl` is absent. |
| Non-streaming continual pretraining | `datasets:` with `type: completion` | Fits when a raw-text corpus can be tokenized/preprocessed before training. |
| Streaming continual pretraining | `pretraining_dataset:` with `type: pretrain` | Use for corpora too large to load or preprocess fully. Requires `max_steps`. |

Route preference/RL workflows away from this sub-skill when `rl: dpo`, `rl: kto`, `rl: orpo`, `rl: grpo`, EBFT reward fields, preference datasets, or vLLM generation requirements are central to the task.

## SFT Recipe Flow

1. Select a base model or local model directory in `base_model`. If the model is private or remote, remind the user that Axolotl may need network access and Hugging Face credentials at runtime.
2. Choose a dataset `type`:
   - `chat_template` for OpenAI-style messages or chat-like records.
   - `alpaca` for instruction/input/output rows.
   - `input_output` for direct source/target pairs.
   - `completion` only when every token in the text should be learned rather than masking a prompt.
3. Pick LoRA, QLoRA, or full fine-tune using [training-options.md](training-options.md).
4. Set `output_dir` and, when preprocessing separately, set `dataset_prepared_path` to a stable reusable directory.
5. Set `sequence_len` to a value the model/tokenizer and GPU budget can support. Start smaller for one-GPU experiments.
6. For packed SFT, set `sample_packing: true`, usually `eval_sample_packing: true`, and an attention backend that supports packing such as `attn_implementation: flash_attention_2`.
7. Validate before training:
   - `axolotl preprocess config.yaml` to build/verify prepared data.
   - `axolotl preprocess config.yaml --debug` to inspect tokenization and label masking when using chat templates, `train_on_inputs: false`, or custom formats.
8. Train only after validation: `axolotl train config.yaml`.

## Continual Pretraining Flow

Use continual pretraining for raw text where the whole document is training signal. Do not add instruction masking fields unless the data is actually supervised fine-tuning data.

### Non-Streaming Corpus

Use this when the corpus fits in memory/disk preprocessing and you want tokenized artifacts before training:

```yaml
datasets:
  - path: ./domain_corpus.jsonl
    type: completion
    field: text
sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true
attn_implementation: flash_attention_2
```

Recommended sequence:

1. Run `axolotl preprocess config.yaml` to tokenize and verify the completion corpus.
2. Reuse `dataset_prepared_path` for repeated attempts with the same model/tokenizer/dataset settings.
3. Run `axolotl train config.yaml` after data validation.

### Streaming Corpus

Use this when the corpus is too large to preprocess fully or should be consumed on demand:

```yaml
pretraining_dataset:
  - path: HuggingFaceFW/fineweb-edu
    type: pretrain
    text_column: text
    split: train
max_steps: 1000
streaming_multipack_buffer_size: 10000
sample_packing: true
pretrain_multipack_attn: true
```

Key constraints:

- `max_steps` is required because the trainer cannot infer the length of an iterable dataset.
- `val_set_size` is not supported with `pretraining_dataset`; use an explicit evaluation strategy outside this minimal recipe when needed.
- `group_by_length` does not fit streaming pretraining.
- `pretrain_multipack_attn: true` prevents cross-attention between packed pretraining samples.

## Checkpoint and Resume Workflow

Axolotl writes training outputs to `output_dir`; checkpoint cadence is controlled with fields such as `save_steps`, `saves_per_epoch`, `save_strategy`, `save_total_limit`, and dynamic checkpoint settings.

Use one resume strategy at a time:

```yaml
resume_from_checkpoint: ./outputs/run/checkpoint-500
```

or:

```yaml
auto_resume_from_checkpoints: true
```

Axolotl’s resume utility looks for numeric `checkpoint-*` directories under `output_dir`; with `auto_resume_from_checkpoints: true`, it chooses the highest numeric checkpoint when `resume_from_checkpoint` is unset.

Dynamic checkpoints are enabled by config and triggered by creating a trigger file inside `output_dir` during training:

```yaml
dynamic_checkpoint:
  enabled: true
  check_interval: 100
  trigger_file_path: axolotl_checkpoint.save
```

Interactive `Ctrl+C` saves model weights and exits gracefully, but does not necessarily preserve optimizer state for a resumable checkpoint. Prefer scheduled or dynamic checkpoints when resume fidelity matters.

## Validation Before Expensive Runs

Use this order unless the user explicitly asks for a different flow:

1. Static review of YAML fields: no `rl`, has either `datasets` or `pretraining_dataset`, has `base_model`, has `output_dir`, has `learning_rate`, and has `micro_batch_size` plus `gradient_accumulation_steps`.
2. For QLoRA, ensure `adapter: qlora` and `load_in_4bit: true`; do not combine QLoRA training with `load_in_8bit`.
3. For 8-bit LoRA, use `adapter: lora` with `load_in_8bit: true` when desired.
4. For full fine-tune, omit `adapter`, `load_in_4bit`, and `load_in_8bit`.
5. For streaming or `pretraining_dataset`, ensure `max_steps` is set.
6. For sample packing, prefer `pad_to_sequence_len: true` and a packing-compatible attention backend.
7. Run `axolotl preprocess config.yaml --debug` for supervised datasets before long training runs when masking or chat formatting might be wrong.

## After Training

- For LoRA/QLoRA adapter inference, use the same YAML and pass the adapter output directory through the inference command expected by the surrounding Axolotl CLI workflow.
- To merge LoRA weights into a base model, use `axolotl merge-lora config.yaml` after training; merged output is produced under the configured output tree.
- Keep the same config as the source of truth for train, preprocess, inference, and merge operations.
