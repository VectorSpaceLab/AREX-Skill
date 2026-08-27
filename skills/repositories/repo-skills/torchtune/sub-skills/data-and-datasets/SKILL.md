---
name: data-and-datasets
description: "Build and validate torchtune dataset configs, message transforms,
  packing, prompt templates, multimodal rows, and collators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# data-and-datasets

Use this sub-skill when a torchtune task is about dataset shape, `Message` conversion, input masking, local or Hugging Face data sources, sample packing, prompt templates, multimodal text+image rows, or batch collation.

## Route Tasks

- Choose `instruct_dataset` or `InputOutputToMessages` for single-turn `input`/`output` SFT rows.
- Choose `chat_dataset`, `ShareGPTToMessages`, or `OpenAIToMessages` for multi-turn conversations.
- Choose `preference_dataset` or `ChosenRejectedToMessages` for DPO/reward data with `chosen` and `rejected` conversations.
- Choose `text_completion_dataset` for free-form pretraining-style corpora with a text column.
- Choose `torchtune.datasets.multimodal` builders for text+image SFT rows, and keep image handling in the dataset/model transform boundary.
- Choose `PackedDataset` only when the tokenizer or model transform has `max_seq_len` and the recipe expects packed SFT/text-completion batches.

## Standard Workflow

1. Identify the raw row shape and source: Hugging Face dataset name, local `json`/`jsonl`/`csv`/`text`, or remote file URL.
2. Map raw columns to the expected torchtune keys with `column_map`, `conversation_column`, or builder-specific arguments.
3. Convert rows to `Message` lists before tokenization; validate role order and non-empty content early.
4. Pair the dataset builder with the correct tokenizer or model transform from [models-and-modules](../models-and-modules/SKILL.md).
5. Decide masking with `masking_strategy` where exposed, or legacy `train_on_input` when using builder config fields.
6. Decide packing and collation after verifying tokenized sample keys match the target recipe in [post-training-recipes](../post-training-recipes/SKILL.md).
7. Use [cli-and-config](../cli-and-config/SKILL.md) for `tune cp`, `tune cat`, `tune validate`, registry names, and launch syntax; do not import `recipes` as a Python package.

## References

- [Data formats](references/data-formats.md) explains row shapes, YAML fragments, packing, prompt templates, collators, and local/HF source assumptions.
- [API reference](references/api-reference.md) lists the practical torchtune data and dataset signatures agents usually need.
- [Troubleshooting](references/troubleshooting.md) maps common data failures to fixes.
- [JSONL validator](scripts/validate_messages_jsonl.py) checks message, input-output, chat, and preference rows without training or downloads.

## Quick Validation

From this sub-skill directory, run the bundled validator on a local JSONL sample before wiring it into a recipe:

```bash
python scripts/validate_messages_jsonl.py data/sample.jsonl --shape auto
```

For multimodal rows with local image paths:

```bash
python scripts/validate_messages_jsonl.py data/sample.jsonl --shape conversations --image-key image --image-root data --check-image-paths
```

The validator is intentionally lightweight: it parses JSONL, checks required columns, checks message role/content structure, optionally checks local image paths, and never imports torch, starts training, or downloads datasets.
