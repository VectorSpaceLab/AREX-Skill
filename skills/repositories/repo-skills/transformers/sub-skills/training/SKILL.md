---
name: training
description: "Create Transformers Trainer, TrainingArguments, data-collator,
  example-script, distributed, checkpoint/resume, Hub push, and safe fine-tuning
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Transformers Training

Use this sub-skill when the task is to fine-tune, evaluate during training, resume checkpoints, configure `Trainer` or `Seq2SeqTrainer`, adapt PyTorch example scripts, choose collators, or validate `TrainingArguments` before a run.

Transformers inspected version: `5.13.0.dev0`. Import package: `transformers`. Training APIs are PyTorch-dependent; environments with only the base `transformers` import may raise optional dependency `ImportError` for `Trainer`, `TrainingArguments`, model classes, or collators until `torch` and task extras are installed.

## Route Here

- Build `TrainingArguments`, `Seq2SeqTrainingArguments`, `Trainer`, or `Seq2SeqTrainer` workflows.
- Convert an inference checkpoint into a fine-tuning plan with model/tokenizer/collator validation.
- Adapt a bundled example-script command pattern for text classification, token classification, causal LM, masked LM, summarization, translation, QA, vision, audio, or segmentation.
- Decide between the `Trainer` route and a `*_no_trainer.py`/Accelerate custom-loop route.
- Configure evaluation cadence, checkpoint saves, `load_best_model_at_end`, resume, mixed precision, `torch_compile`, FSDP, DeepSpeed, or Hub push.
- Diagnose training failures around missing dependencies, labels, collators, padding, `remove_unused_columns`, checkpoints, OOM, or distributed launch.

## Route Elsewhere

- Inference-only `pipeline(...)`, `device_map`, or dtype loading choices: [inference-pipelines](../inference-pipelines/SKILL.md).
- Text generation decoding, streamers, chat templates, or `GenerationConfig`: [generation](../generation/SKILL.md).
- Tokenizer, processor, image/audio/video preprocessing details outside training batches: [tokenizers-processors](../tokenizers-processors/SKILL.md).
- `transformers` CLI usage or serving entrypoints: [serving-cli](../serving-cli/SKILL.md).
- Quantization, PEFT, bitsandbytes, AWQ/GPTQ, or backend integration details: [quantization-integrations](../quantization-integrations/SKILL.md).
- Adding a new model architecture, config, processor, or modular model implementation: [model-extension](../model-extension/SKILL.md).

## Fast Workflow

1. Identify task shape: classification, token classification, language modeling, seq2seq, QA, vision, audio, or custom model.
2. Choose route: `Trainer` for standard supervised fine-tuning; no-trainer/Accelerate for custom optimizer/scheduler loops or fully manual loss handling.
3. Verify dependencies: `torch` for training, usually `accelerate` for device/distributed orchestration, `datasets` for example scripts, and `evaluate` for metrics.
4. Load matching components: `AutoConfig`, `AutoTokenizer` or task processor, `AutoModelFor*`, and a task-appropriate data collator.
5. Normalize datasets to model inputs and labels; confirm `Trainer` sees every column required by `model.forward(...)` or set `remove_unused_columns=False`.
6. Configure `TrainingArguments` with output, batch sizes, eval/save/log strategies, precision, checkpoint retention, distributed options, and Hub behavior.
7. Dry-run with tiny sample limits or a smoke script before long training.
8. Train, evaluate, save, resume if needed, and push only when authentication and repository names are deliberate.

## Primary References

- [API reference](references/api-reference.md): class names, constructor fields, collators, validation checks, and smoke script usage.
- [Task recipes](references/task-recipes.md): command/API patterns for common fine-tuning tasks and example-script adaptation.
- [Distributed training](references/distributed-training.md): `torchrun`, Accelerate, FSDP, DeepSpeed, mixed precision, compile, and OOM decisions.
- [Troubleshooting](references/troubleshooting.md): failure mode diagnosis and fixes.

## Trainer Skeleton

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, Trainer, TrainingArguments

model_name = "distilbert/distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

args = TrainingArguments(
    output_dir="outputs/text-classifier",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    learning_rate=2e-5,
    num_train_epochs=3,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer),
)
trainer.train(resume_from_checkpoint=None)
```

## Safe Argument Validation

Use the bundled no-network smoke helper before launching expensive jobs:

```bash
python scripts/training_args_smoke.py \
  --output_dir outputs/smoke \
  --per_device_train_batch_size 2 \
  --per_device_eval_batch_size 2 \
  --eval_strategy steps \
  --eval_steps 50 \
  --save_strategy steps \
  --save_steps 100 \
  --load_best_model_at_end \
  --metric_for_best_model eval_loss \
  --report_to none
```

Expected signal: it either prints normalized `TrainingArguments` decisions or clearly reports the missing optional dependency that blocks instantiation.

## Required Preflight Checks

- `eval_strategy="steps"` needs nonzero `eval_steps`; if `eval_steps` is omitted, confirm fallback to `logging_steps` is intentional.
- `load_best_model_at_end=True` requires evaluation and compatible saving; align `eval_strategy` and `save_strategy` or use `save_strategy="best"` with a metric.
- `save_steps` must be a round multiple of `eval_steps` when loading the best model with step-based strategies.
- Custom labels need model-compatible names; use `label_names=[...]` for multiple label tensors and avoid a label argument literally named `label`.
- If examples include columns not consumed by the model, either remove them during preprocessing or set `remove_unused_columns=False` and make the collator/model handle them.
- Dynamic padding needs a tokenizer/processor with a pad token; causal LM often needs `tokenizer.pad_token = tokenizer.eos_token` if no pad token exists.
- Hub push needs authentication and intentional `hub_model_id`; avoid `push_to_hub=True` in local smoke tests unless publishing is desired.

## Example-Script Route

Prefer example-script style when the task already maps to a maintained script pattern. The public command shape is:

```bash
python ./train_task.py \
  --model_name_or_path MODEL_OR_LOCAL_DIR \
  --dataset_name DATASET \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/task-smoke \
  --per_device_train_batch_size 4 \
  --per_device_eval_batch_size 4
```

For self-contained skills, do not require future agents to open original repo example files. Distill the required flags into the task plan and ask the user for local script/file locations only when executing in their project.

## Outputs To Return

For training tasks, return the selected route, dependencies, model/tokenizer/collator choices, exact command or API skeleton, validation checks, expected logs/metrics, resume/publish behavior, and any remaining hardware risk.
