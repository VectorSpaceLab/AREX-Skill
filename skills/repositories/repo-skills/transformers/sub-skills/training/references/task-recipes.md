# Training Task Recipes

Use these recipes to synthesize concrete fine-tuning commands or API scaffolds without depending on the original Transformers repository files at runtime. Ask the user for their local script location only if they already have a copied/adapted script in their project.

## Route Selection

Choose `Trainer` when:

- The model returns a loss from standard inputs and labels.
- The task maps to a common supervised recipe.
- Evaluation, checkpointing, logging, Hub push, and distributed features should be handled by framework defaults.
- The user wants concise code and fewer custom-loop responsibilities.

Choose a no-trainer/Accelerate route when:

- The loss has custom multi-step logic that does not fit `compute_loss` or a simple subclass.
- The optimizer, scheduler, gradient updates, or distributed synchronization need full manual control.
- The user is adapting an example script ending in `_no_trainer.py`.
- The project already uses `accelerate launch` and a custom loop.

Choose a hand-written PyTorch loop only when neither `Trainer` nor Accelerate example patterns fit. In that case, keep Transformers responsibilities to model/config/tokenizer/collator loading and route custom training-loop design outside this sub-skill.

## Universal Preprocessing Checks

Before building a command or `Trainer`:

1. Identify input columns and target columns.
2. Tokenize/process inputs with truncation and an explicit max length when examples can be long.
3. Remove unused raw columns during dataset mapping when they are no longer needed.
4. Keep required custom columns only if the collator/model consumes them; otherwise they may be pruned by `remove_unused_columns=True`.
5. Confirm label names and shapes match the model head.
6. Choose a collator that pads both model inputs and labels correctly.
7. Run with small sample limits first when using example-script style.

## Text Classification

Use `AutoModelForSequenceClassification`, `AutoTokenizer`, and `DataCollatorWithPadding`.

API skeleton:

```python
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
data_collator = DataCollatorWithPadding(tokenizer)
```

Command pattern:

```bash
python ./train_text_classification.py \
  --model_name_or_path distilbert/distilbert-base-uncased \
  --train_file train.csv \
  --validation_file valid.csv \
  --text_column_name text \
  --label_column_name label \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/text-classification-smoke \
  --per_device_train_batch_size 8 \
  --per_device_eval_batch_size 8
```

Validation signals:

- Classification head `num_labels` equals dataset label count.
- Use `--ignore_mismatched_sizes` only when intentionally replacing an incompatible head.
- For multi-label classification, labels should be multi-hot or compatible with the script/model loss expectations.

## Token Classification

Use `AutoModelForTokenClassification` and `DataCollatorForTokenClassification`.

Command pattern:

```bash
python ./train_token_classification.py \
  --model_name_or_path bert-base-cased \
  --dataset_name conll2003 \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/token-classification-smoke \
  --per_device_train_batch_size 8 \
  --per_device_eval_batch_size 8
```

Validation signals:

- Word-piece label alignment maps non-first subtokens to `-100` unless training should supervise all subtokens.
- `label_list`, `id2label`, and `label2id` are consistent with the dataset.
- Collator pads token labels with the ignore index.

## Causal Language Modeling

Use `AutoModelForCausalLM` and `DataCollatorForLanguageModeling(mlm=False)`.

API decisions:

- If the tokenizer has no pad token, set `tokenizer.pad_token = tokenizer.eos_token` when acceptable for batching.
- Use `dtype="auto"` when loading weights to avoid unnecessary fp32 memory expansion.
- Use block/grouping logic for long text corpora; do not feed raw unbounded strings directly.

Command pattern:

```bash
python ./train_causal_lm.py \
  --model_name_or_path gpt2 \
  --train_file train.txt \
  --validation_file valid.txt \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/clm-smoke \
  --per_device_train_batch_size 2 \
  --per_device_eval_batch_size 2
```

Validation signals:

- `block_size` fits memory.
- Padding token decisions are explicit.
- OOM risk is handled with smaller batch size, gradient accumulation, checkpointing, and mixed precision.

## Masked Language Modeling

Use `AutoModelForMaskedLM` and `DataCollatorForLanguageModeling(mlm=True)`.

Command pattern:

```bash
python ./train_masked_lm.py \
  --model_name_or_path bert-base-uncased \
  --train_file train.txt \
  --validation_file valid.txt \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/mlm-smoke \
  --per_device_train_batch_size 8 \
  --per_device_eval_batch_size 8
```

Validation signals:

- Tokenizer has a mask token.
- `mlm_probability` is deliberate.
- Whole-word masking requires a compatible tokenizer and collator path.

## Summarization And Translation

Use `AutoModelForSeq2SeqLM`, `Seq2SeqTrainer`, `Seq2SeqTrainingArguments`, and `DataCollatorForSeq2Seq`.

Command pattern:

```bash
python ./train_summarization.py \
  --model_name_or_path google-t5/t5-small \
  --dataset_name cnn_dailymail \
  --dataset_config 3.0.0 \
  --source_prefix "summarize: " \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 --max_predict_samples 50 \
  --predict_with_generate \
  --output_dir outputs/summarization-smoke \
  --per_device_train_batch_size 4 \
  --per_device_eval_batch_size 4 \
  --eval_strategy steps --eval_steps 100 \
  --save_strategy steps --save_steps 100 \
  --load_best_model_at_end \
  --metric_for_best_model eval_loss
```

Translation differs mainly by source/target language columns and optional prefixes:

```bash
python ./train_translation.py \
  --model_name_or_path google-t5/t5-small \
  --source_lang en --target_lang ro \
  --train_file train.json --validation_file valid.json \
  --do_train --do_eval --predict_with_generate \
  --output_dir outputs/translation-smoke
```

Validation signals:

- `predict_with_generate=True` if metrics require decoded predictions.
- Label padding uses `-100` where loss should ignore pad positions.
- `source_prefix` is included for T5-style summarization/translation prompts when needed.
- Eval/save cadence is compatible before `load_best_model_at_end=True`.

## Question Answering

Use `AutoModelForQuestionAnswering`, tokenizer overflow handling, and span labels.

Command pattern:

```bash
python ./train_question_answering.py \
  --model_name_or_path distilbert/distilbert-base-uncased \
  --dataset_name squad \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/qa-smoke \
  --per_device_train_batch_size 8 \
  --per_device_eval_batch_size 8
```

Validation signals:

- Preprocessing creates `start_positions` and `end_positions`.
- Use `label_names=["start_positions", "end_positions"]` if a custom trainer path drops labels.
- Overflow mappings preserve example IDs for post-processing.

## Vision, Audio, And Segmentation

Use task-specific processors and collators. Common patterns:

- Image classification: `AutoImageProcessor`, `AutoModelForImageClassification`, transforms, pixel-value batches.
- Object detection/segmentation: processor/collator must preserve target dictionaries and image sizes; often set `remove_unused_columns=False`.
- Audio classification/speech recognition: processor or feature extractor handles sampling rate, padding, and labels; seq2seq speech uses generation-aware evaluation.

Validation signals:

- Processor output keys (`pixel_values`, `input_values`, `labels`, target dicts) match `model.forward(...)`.
- Raw image/audio columns are either transformed before `Trainer` or preserved for a custom collator.
- Metrics decode or post-process predictions in the same shape the model emits.

## Converting Pipeline Choice To Fine-Tuning

When a user starts from an inference model or `pipeline(...)` choice:

1. Capture task, model ID/path, revision, trust policy, dtype, and processor/tokenizer choices from the inference plan.
2. Map pipeline task to training model class: sequence classification, token classification, causal LM, seq2seq LM, QA, image classification, etc.
3. Load config first and check architecture/head compatibility.
4. Build tokenizer/processor with the same revision and trust policy.
5. Select a collator and validate pad/label behavior.
6. Build a tiny smoke command with sample limits before full training.

Cross-link: if pipeline loading details are unclear, use [inference-pipelines](../../inference-pipelines/SKILL.md) first, then return here for training.

## Hub Push And Artifacts

For local-only development:

```python
TrainingArguments(output_dir="outputs/local", push_to_hub=False, report_to="none")
```

For publishing:

```python
TrainingArguments(
    output_dir="outputs/my-model",
    push_to_hub=True,
    hub_model_id="namespace/my-model",
    hub_strategy="every_save",
)
```

Expected artifacts include model weights, config, tokenizer/processor files when passed as `processing_class`, trainer state, and checkpoints. Do not enable publishing in examples unless the user has confirmed authentication and target repository ownership.
