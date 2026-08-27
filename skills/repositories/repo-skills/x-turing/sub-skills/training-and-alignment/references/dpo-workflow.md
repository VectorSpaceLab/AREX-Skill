# DPO workflow

## What DPO is for

Direct Preference Optimization aligns a causal model using pairs of preferred and rejected answers. In xTuring, the entry point is `model.dpo_finetune(...)`.

`model.dpo_finetune(...)` builds a `DPOTrainer` under the hood.

Use DPO when you already have preference data and want the model to move toward the chosen response without training a separate reward model.

## Required dataset schema

Create a `PreferenceDataset` with exactly these columns:

- `prompt`
- `chosen`
- `rejected`

Accepted inputs include a dictionary, a Hugging Face dataset, a dataset dict, a saved dataset directory, or a JSONL file with those exact keys.

```python
from xturing.datasets import PreferenceDataset
from xturing.models import BaseModel

preference_data = {
    "prompt": ["Explain gravity simply."],
    "chosen": ["Gravity is the pull that makes objects fall toward each other."],
    "rejected": ["Gravity is a rumor caused by the moon."],
}

dataset = PreferenceDataset(preference_data)
model = BaseModel.create("qwen3_0_6b_lora")
model.dpo_finetune(dataset=dataset, beta=0.1)
```

## What the collator and trainer do

The preference collator turns each sample into two tokenized sequences:

- `chosen_input_ids`, `chosen_attention_mask`, `chosen_labels`
- `rejected_input_ids`, `rejected_attention_mask`, `rejected_labels`

Prompt tokens are masked so the loss only uses the response region.

The DPO trainer then:

1. Deep-copies the policy model into a frozen reference model.
2. Computes log-probabilities for the chosen and rejected responses.
3. Applies the DPO loss.
4. Logs `loss` and `reward_margin`.

Because the reference model stays in memory, DPO is more memory-intensive than plain supervised fine-tuning. Adapter-based models are usually the safest starting point.

## Beta selection

`beta` controls how strongly the policy is kept near the reference model.

- Lower beta: stronger preference shift
- Higher beta: more conservative update

The default is `0.1`, which is a good first check for most small runs.

## Trainer and config behavior

DPO uses the same finetuning config object as SFT, so the same knobs still matter:

- `batch_size`
- `gradient_accumulation_steps`
- `learning_rate`
- `max_length`
- `num_train_epochs`
- `logging_steps`
- `max_grad_norm`
- `save_total_limit`
- `optimizer_name`
- `output_dir`
- `use_deepspeed`
- `deepspeed_config_path`

Important rules:

- `model.dpo_finetune(...)` requires a `PreferenceDataset`.
- LoRA-based DPO routes through DeepSpeed automatically.
- `cpu_adam` requires DeepSpeed.
- If you enable a custom DeepSpeed config, pass it through `deepspeed_config_path`.

## When to prefer DPO over SFT

Use DPO when:

- you have pairwise preference data
- you want to preserve fluent generation while nudging style or ranking
- you can afford the extra memory from the frozen reference model

Use SFT when:

- you only have target completions
- you want a simpler and cheaper training run
- you are still preparing or normalizing your preference data

## Sanity check after DPO

After training, run one or two short generations on prompts that were not in the preference set. If the adapter learned the intended style shift, save the model and keep the prompt / chosen / rejected schema around for later replay.
