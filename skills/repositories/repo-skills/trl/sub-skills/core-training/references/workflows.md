# Core Training Workflows

These workflows are safe skeletons for agents to adapt. They do not depend on original repository examples and omit long-running launch commands.

## Choose the Trainer

| Goal | Trainer | Required dataset shape | Required extras |
| --- | --- | --- | --- |
| Instruction tune or continue supervised training | `SFTTrainer` | `text`, `prompt`/`completion`, or conversational messages | Optional `formatting_func`, optional PEFT |
| Optimize from accepted/rejected answers | `DPOTrainer` | `prompt`, `chosen`, `rejected` or conversational equivalents | Optional `ref_model`, optional PEFT |
| Train a reward model | `RewardTrainer` | `chosen`, `rejected` | Sequence-classification-compatible model |
| Online RL with grouped completions | `GRPOTrainer` | `prompt` plus reward columns | At least one `reward_funcs` entry |
| Online RL with leave-one-out baseline | `RLOOTrainer` | `prompt` plus reward columns | At least one `reward_funcs` entry |

For mixed projects with prompt-completion data and preference data, do not force one trainer across all splits. Typical sequence: SFT on prompt-completion data, DPO on preference pairs, then optionally RewardTrainer/GRPO/RLOO if online reward optimization is needed.

## Shared Model and Config Setup

```python
from trl import ModelConfig
from trl.trainer.utils import get_kbit_device_map, get_peft_config, get_quantization_config

model_args = ModelConfig(
    model_name_or_path="Qwen/Qwen2.5-0.5B-Instruct",
    trust_remote_code=False,
    use_peft=False,
)

model_init_kwargs = {
    "revision": model_args.model_revision,
    "trust_remote_code": model_args.trust_remote_code,
    "attn_implementation": model_args.attn_implementation,
    "torch_dtype": model_args.torch_dtype,
    "use_cache": False,
}
quantization_config = get_quantization_config(model_args)
if quantization_config is not None:
    model_init_kwargs["quantization_config"] = quantization_config
    model_init_kwargs["device_map"] = get_kbit_device_map()

peft_config = get_peft_config(model_args)
```

Use this pattern in script-like code when you need to mirror TRL launchers. For simple Python snippets, passing `model="model-id"` directly to the trainer is enough.

## SFT Workflow

```python
from datasets import Dataset
from trl import SFTConfig, SFTTrainer

train_dataset = Dataset.from_list([
    {"prompt": "Explain RLHF in one sentence.", "completion": "RLHF aligns a model using human or reward feedback."},
])

args = SFTConfig(
    output_dir="runs/sft",
    max_length=1024,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-5,
    completion_only_loss=True,
)

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    args=args,
    train_dataset=train_dataset,
)
# trainer.train()
```

Checklist:

- For plain text data, use `dataset_text_field="text"` or provide `formatting_func`.
- For prompt-completion data, set `completion_only_loss=True` when prompt tokens should not train the model.
- For conversational data, use `assistant_only_loss=True` only after confirming assistant masks are available.
- If sequences are mostly short, consider `packing=True`; route packing/data-shape conversion to `../data-and-rewards/` when examples are nested.

## DPO Workflow

```python
from datasets import Dataset
from trl import DPOConfig, DPOTrainer

train_dataset = Dataset.from_list([
    {
        "prompt": "Write a safe password tip.",
        "chosen": "Use a unique password and a password manager.",
        "rejected": "Reuse an easy password everywhere.",
    },
])

args = DPOConfig(
    output_dir="runs/dpo",
    beta=0.1,
    max_length=1024,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=1e-6,
)

trainer = DPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    ref_model=None,
    args=args,
    train_dataset=train_dataset,
)
# trainer.train()
```

Checklist:

- Ensure each row has exactly one preferred and one rejected response.
- Use `ref_model=None` for the default reference behavior unless a separate reference model is intentionally required.
- Adjust `beta` before changing loss families; higher `beta` keeps policy updates closer to the reference.
- For noisy preferences, consider `label_smoothing` with robust/exo-style losses.

## Reward Modeling Workflow

```python
from datasets import Dataset
from trl import RewardConfig, RewardTrainer

train_dataset = Dataset.from_list([
    {"chosen": "Clear and helpful answer.", "rejected": "Vague answer."},
])

args = RewardConfig(
    output_dir="runs/reward",
    max_length=1024,
    per_device_train_batch_size=2,
    learning_rate=1e-4,
)

trainer = RewardTrainer(
    model="Qwen/Qwen2.5-0.5B",
    args=args,
    train_dataset=train_dataset,
)
# trainer.train()
```

Checklist:

- Use a reward-model-compatible checkpoint or let TRL load a sequence classification head.
- Keep `max_length` high enough to include the distinguishing content in both candidates.
- Use `center_rewards_coefficient` only when reward centering is an explicit objective.

## GRPO Workflow

```python
from datasets import Dataset
from trl import GRPOConfig, GRPOTrainer

train_dataset = Dataset.from_list([
    {"prompt": "What is 2+2?", "answer": "4", "task_type": "math"},
])

def correctness_reward(prompts, completions, answer, task_type=None, **kwargs):
    rewards = []
    for completion, expected, kind in zip(completions, answer, task_type or [None] * len(completions)):
        if kind != "math":
            rewards.append(None)
        else:
            rewards.append(1.0 if str(expected) in completion else 0.0)
    return rewards

args = GRPOConfig(
    output_dir="runs/grpo",
    num_generations=4,
    max_completion_length=128,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
    learning_rate=1e-6,
    remove_unused_columns=False,
)

trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[correctness_reward],
    args=args,
    train_dataset=train_dataset,
)
# trainer.train()
```

Checklist:

- `reward_funcs` is mandatory; never instantiate GRPO without it.
- Effective batch size must divide evenly by `num_generations`.
- Leave `remove_unused_columns=False` when rewards need fields like `answer` or `task_type`.
- If all rewards return `None` for a row, the row is unscorable; add a fallback reward or fix task routing.
- Route vLLM, multi-GPU, and memory planning to `../scaling-and-backends/`.

## RLOO Workflow

```python
from datasets import Dataset
from trl import RLOOConfig, RLOOTrainer

train_dataset = Dataset.from_list([
    {"prompt": "Name one primary color.", "answers": ["red", "blue", "yellow"]},
])

def answer_reward(prompts, completions, answers, **kwargs):
    return [1.0 if any(answer in completion.lower() for answer in row_answers) else 0.0 for completion, row_answers in zip(completions, answers)]

args = RLOOConfig(
    output_dir="runs/rloo",
    num_generations=2,
    max_completion_length=128,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=1,
    learning_rate=1e-6,
    beta=0.05,
    remove_unused_columns=False,
)

trainer = RLOOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[answer_reward],
    args=args,
    train_dataset=train_dataset,
)
# trainer.train()
```

Checklist:

- Use a standard dataset, not an iterable dataset.
- Keep `num_generations` at least `2` for meaningful leave-one-out comparisons during training.
- Set `beta=0.0` only when intentionally avoiding the reference model.
- Like GRPO, preserve reward columns with `remove_unused_columns=False`.

## Script-Style Workflow

Stable TRL launchers follow this shape:

```python
from trl import ModelConfig, SFTConfig, SFTTrainer, TrlParser
from trl.trainer.utils import get_peft_config

parser = TrlParser((SFTConfig, ModelConfig))
training_args, model_args = parser.parse_args_and_config()
trainer = SFTTrainer(
    model=model_args.model_name_or_path,
    args=training_args,
    train_dataset=train_dataset,
    peft_config=get_peft_config(model_args),
)
trainer.train()
```

For actual command construction and YAML recipes, use `../cli-and-configs/`. For scaling flags, use `../scaling-and-backends/`.
