# Stable Trainer API Reference

This reference covers TRL 1.7.0.dev0 stable post-training trainers. It is intentionally concise: use it to choose the trainer and instantiate the correct object without reopening repository docs.

## Common Construction Pattern

```python
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer

train_dataset = load_dataset("your-dataset", split="train")
args = SFTConfig(output_dir="runs/sft", learning_rate=2e-5, max_length=1024)
trainer = SFTTrainer(model="Qwen/Qwen2.5-0.5B", args=args, train_dataset=train_dataset)
trainer.train()
```

Common rules:

- `model` can be a model id string, a loaded `PreTrainedModel`, or a PEFT model for all five stable trainers.
- If `model` is a string, trainer-specific `model_init_kwargs` may be used through the config; if `model` is already instantiated, do not pass `model_init_kwargs`.
- `processing_class` can usually be omitted so TRL loads the matching tokenizer/processor; ensure a pad token exists for generation and reward-model paths.
- `peft_config` is accepted by all five trainers; advanced PEFT/quantization/device details belong in `../scaling-and-backends/`.
- `eval_dataset` accepts a dataset, iterable dataset where supported, or a dictionary of evaluation datasets.

## SFTTrainer

Use for supervised fine-tuning and instruction tuning.

```python
from trl import SFTConfig, SFTTrainer

args = SFTConfig(
    output_dir="runs/sft",
    learning_rate=2e-5,
    max_length=1024,
    dataset_text_field="text",
    packing=False,
)
trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    args=args,
    train_dataset=train_dataset,
    formatting_func=None,
)
```

Verified constructor shape:

```text
SFTTrainer(model, args=None, data_collator=None, train_dataset=None, eval_dataset=None, processing_class=None, compute_loss_func=None, compute_metrics=None, callbacks=None, optimizers=(None, None), optimizer_cls_and_kwargs=None, preprocess_logits_for_metrics=None, peft_config=None, formatting_func=None)
```

Default highlights:

- `SFTConfig.learning_rate=2e-5`
- `dataset_text_field="text"`
- `max_length=1024`; set `None` only when intentionally disabling truncation.
- `packing=False`; packing groups examples into fixed-length blocks using `max_length`.
- `completion_only_loss=None`; prompt-completion datasets default to completion-only loss, plain LM datasets default to full-sequence loss.
- `assistant_only_loss=False`; use only for conversational datasets where assistant-token masks are available.
- `padding_free=False`; requires compatible attention kernels when enabled.
- `loss_type=None`; normally resolves to memory-aware NLL behavior.

Expected datasets:

- Language-modeling shape: a text column such as `text`.
- Prompt-completion shape: columns such as `prompt` and `completion`.
- Conversational shape: message lists; route conversion details to `../data-and-rewards/`.

## DPOTrainer

Use for direct preference optimization from paired responses.

```python
from trl import DPOConfig, DPOTrainer

args = DPOConfig(output_dir="runs/dpo", learning_rate=1e-6, beta=0.1, max_length=1024)
trainer = DPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    ref_model=None,
    args=args,
    train_dataset=preference_dataset,
)
```

Verified constructor shape:

```text
DPOTrainer(model, ref_model=None, args=None, data_collator=None, train_dataset=None, eval_dataset=None, processing_class=None, compute_metrics=None, callbacks=None, optimizers=(None, None), peft_config=None)
```

Default highlights:

- `DPOConfig.learning_rate=1e-6`
- `max_length=1024`
- `beta=0.1`; higher values constrain the policy closer to the reference model.
- `loss_type=["sigmoid"]`; alternatives include `hinge`, `ipo`, `robust`, `exo_pair`, `nca_pair`, `aot`, `apo_zero`, and related pairwise objectives.
- `label_smoothing=0.0`
- `sync_ref_model=False`; not compatible with common PEFT/precomputed-reference setups.

Expected datasets:

- Preference rows with a prompt plus `chosen` and `rejected`, or conversational equivalents.
- If the dataset contains mixed prompt-completion and preference fields, use DPO only for the preference split and route conversion to `../data-and-rewards/`.

## RewardTrainer

Use to train a reward model from pairwise preferences.

```python
from trl import RewardConfig, RewardTrainer

args = RewardConfig(output_dir="runs/reward", learning_rate=1e-4, max_length=1024)
trainer = RewardTrainer(
    model="Qwen/Qwen2.5-0.5B",
    args=args,
    train_dataset=reward_dataset,
)
```

Verified constructor shape:

```text
RewardTrainer(model, args=None, data_collator=None, train_dataset=None, eval_dataset=None, processing_class=None, compute_metrics=None, callbacks=None, optimizers=(None, None), optimizer_cls_and_kwargs=None, preprocess_logits_for_metrics=None, peft_config=None)
```

Default highlights:

- `RewardConfig.learning_rate=1e-4`
- `max_length=1024`; reward inputs truncate from the right.
- `center_rewards_coefficient=None`; set a small value such as `0.01` only when mean-zero reward regularization is desired.

Expected datasets:

- Pairwise preference rows containing `chosen` and `rejected` text or conversations.
- The model should be compatible with sequence classification or be loadable in that form.

## GRPOTrainer

Use for online RL where completions are generated and scored by reward functions or reward models.

```python
from trl import GRPOConfig, GRPOTrainer

def reward_len(prompts, completions, **kwargs):
    return [float(len(completion)) for completion in completions]

args = GRPOConfig(
    output_dir="runs/grpo",
    learning_rate=1e-6,
    num_generations=8,
    max_completion_length=256,
)
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[reward_len],
    args=args,
    train_dataset=prompt_dataset,
)
```

Verified constructor shape:

```text
GRPOTrainer(model, reward_funcs, args=None, train_dataset=None, eval_dataset=None, processing_class=None, reward_processing_classes=None, callbacks=None, optimizers=(None, None), peft_config=None, tools=None, rollout_func=None, environment_factory=None)
```

Default highlights:

- `GRPOConfig.learning_rate=1e-6`
- `remove_unused_columns=False`; keep it false when reward functions need extra dataset columns.
- `num_generations=8`; effective batch size must be divisible by this value.
- `max_completion_length=256`
- `generation_batch_size=None`; defaults from effective training batch and `steps_per_generation`.
- `steps_per_generation=None`; defaults to `gradient_accumulation_steps`.
- `beta=0.0`; no reference model is loaded unless a nonzero KL coefficient is set.
- `loss_type="dapo"`
- `mask_truncated_completions=False`; enable to exclude truncated completions from loss when this is part of the training design.
- `use_vllm=False`, `vllm_mode="colocate"`; route vLLM setup to `../scaling-and-backends/`.

Expected datasets and rewards:

- Dataset must include `prompt`; extra columns can be consumed by custom rewards when `remove_unused_columns=False`.
- `reward_funcs` is required and can be a callable, model id, model, or list of these.
- Custom reward functions receive `prompts`, `completions`, `completion_ids`, and any preserved dataset columns; they may return `None` for samples they cannot score.

## RLOOTrainer

Use for online RL with a leave-one-out baseline across completions for each prompt.

```python
from trl import RLOOConfig, RLOOTrainer

def reward_contains_answer(prompts, completions, answer, **kwargs):
    return [1.0 if str(a) in completion else 0.0 for completion, a in zip(completions, answer)]

args = RLOOConfig(
    output_dir="runs/rloo",
    learning_rate=1e-6,
    num_generations=2,
    max_completion_length=256,
)
trainer = RLOOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[reward_contains_answer],
    args=args,
    train_dataset=prompt_dataset,
)
```

Verified constructor shape:

```text
RLOOTrainer(model, reward_funcs, args=None, train_dataset=None, eval_dataset=None, processing_class=None, reward_processing_classes=None, callbacks=None, optimizers=(None, None), peft_config=None)
```

Default highlights:

- `RLOOConfig.learning_rate=1e-6`
- `remove_unused_columns=False`
- `num_generations=2`; effective batch size must be divisible by this value.
- `max_completion_length=256`
- `beta=0.05`; set `0.0` to avoid loading a reference model.
- `reward_weights=None`; all rewards weight equally.
- `mask_truncated_completions=False`
- `use_vllm=False`, `vllm_mode="colocate"`; route backend setup to `../scaling-and-backends/`.

Expected datasets and rewards:

- Dataset must include `prompt`; iterable datasets are not supported.
- `reward_funcs` is required and follows the same callable/model pattern as GRPO.
- Rewards returning `None` are treated as unscorable for that sample; every row needs at least one non-`None` reward to provide learning signal.

## ModelConfig Highlights

Training scripts and config-driven workflows commonly pair trainer configs with `ModelConfig`:

- `model_name_or_path=None`; set to a model id or local model directory in script workflows.
- `model_revision="main"`
- `trust_remote_code=False`
- `attn_implementation=None`; values such as `flash_attention_2` require optional packages.
- `use_peft=False`, `lora_r=16`, `lora_alpha=32`
- `load_in_8bit=False`, `load_in_4bit=False`; quantized loading works only with LoRA-style PEFT.
