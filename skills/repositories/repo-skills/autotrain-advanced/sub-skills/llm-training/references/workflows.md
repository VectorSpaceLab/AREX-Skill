# LLM workflows

## Command template

```bash
autotrain llm --train \
  --project-name my-llm-run \
  --model gpt2 \
  --data-path path/or/hub-dataset \
  --trainer sft \
  --text-column text \
  --block_size 1024 \
  --epochs 1 \
  --batch-size 2 \
  --gradient-accumulation 4 \
  --backend local
```

Use `autotrain llm --help` for the exact flag spelling in the active install. `--block_size` is accepted and has the alias `--block-size`; comma-separated values are parsed into a list.

## Config aliases

YAML configs use hyphenated LLM task aliases:

| YAML `task` | Resolved trainer behavior |
| --- | --- |
| `llm` | default/generic language-model training |
| `llm-sft` | supervised finetuning |
| `llm-dpo` | DPO preference training |
| `llm-orpo` | ORPO preference training |
| `llm-reward` | reward-model style training |
| `llm-generic` | default/generic trainer |

The app/API parameter route uses colon keys such as `llm:sft`, `llm:dpo`, and `llm:orpo`. Do not confuse these with the YAML aliases.

## Data columns

Common local CSV/JSONL checks:

- SFT/default: `text_column` is required; default column name is `text`.
- DPO/ORPO/reward: `text_column` and `rejected_text_column` are usually required; `prompt_text_column` is required for prompt/completion preference data.
- If `chat_template` is set, keep prompt/completion formatting consistent with the selected tokenizer template.

Use the text validator for local files:

```bash
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py \
  --task llm \
  --trainer dpo \
  --text-column chosen \
  --rejected-text-column rejected \
  --prompt-text-column prompt \
  data.jsonl
```

For Hub datasets, inspect the dataset columns before launch and mirror the same column names in `data.column_mapping`.

## Config skeleton

```yaml
task: llm-sft
base_model: gpt2
project_name: my-llm-run
log: none
backend: local

data:
  path: path/or/hub-dataset
  train_split: train
  valid_split: null
  chat_template: null
  column_mapping:
    text_column: text
    rejected_text_column: null
    prompt_text_column: null

params:
  block_size: 1024
  model_max_length: 2048
  epochs: 1
  batch_size: 2
  gradient_accumulation: 4
  lr: 3e-5
  peft: true
  quantization: int4
  target_modules: all-linear

hub:
  username: ${HF_USERNAME}
  token: ${HF_TOKEN}
  push_to_hub: false
```

## Backend notes

- `local`, `local-cli`, and `local-ui` run locally and can use local data paths.
- `spaces-*` and `ep-*` require `push_to_hub`, `username`, and `token` in the CLI validation path.
- Large models and quantized workflows may require CUDA, bitsandbytes, flash attention, or unsloth-compatible hardware/packages.

## Adapter flow

- `--merge-adapter` is a training parameter that can merge after training when the trainer supports it.
- For a standalone merge of an existing adapter, use `../model-tools/` and `autotrain tools merge-llm-adapter`.
